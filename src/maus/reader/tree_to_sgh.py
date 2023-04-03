"""
A module to parse Hochfrequenz .tree files and return them as Segment Group Hierarchy
"""
from pathlib import Path
from typing import Union

from more_itertools import first

try:
    from lark import Lark, Tree
except ImportError as import_error:
    import_error.msg += "; Did you install maus[tree]?"
    # lark is only an optional dependency of maus but in this module, it is required
    raise

GRAMMAR = r"""
?start:SEGMENT_GROUP_CHAIN
SEGMENT_GROUP_CHAIN: ROOT_NODE ":" SEGMENT_GROUP ("\n" SEGMENT_GROUP)*
SEGMENT_GROUP: ((SEGMENT_GROUP_KEY) ":"?)? SEGMENT ("," (SEGMENT|SEGMENT_GROUP_REFERENCE))* // e.g. "SG4:CTA[M;M;C*Can3+C*Can17*Can256;C*Ran3{IC}+R*N*Ran256],COM[C;R;M*Man512*Man3;M*Man512*Man3{EM.FX.TE.AJ.AL}]"
SEGMENT_GROUP_REFERENCE: SEGMENT_GROUP_KEY "[" OBLIG_MARK ";" OBLIG_MARK "]"
SEGMENT: SEGMENT_KEY "[" INTERNATIONAL_BDEW_TUPLE_CHAIN "]" // e.g. "CTA[M;M;C*Can3+C*Can17*Can256;C*Ran3{IC}+R*N*Ran256]"
INTERNATIONAL_BDEW_TUPLE_CHAIN: INTERNATIONAL_BDEW_TUPLE (";" INTERNATIONAL_BDEW_TUPLE)* // e.g. "C;R;M*Man512*Man3;M*Man512*Man3{EM.FX.TE.AJ.AL}"
INTERNATIONAL_BDEW_TUPLE: (CONDITIONED_DATA_ELEMENTS_SWITCH*|MULTIPLE_DATA_ELEMENTS";") (CONDITIONED_DATA_ELEMENTS_SWITCH*|MULTIPLE_DATA_ELEMENTS) // f.e. "C*Can3+C*Can17*Can256;C*Ran3{IC}"
CONDITIONED_DATA_ELEMENTS_SWITCH: CONDITION MULTIPLE_DATA_ELEMENTS ["|"]
CONDITION: "(" CONDITION_BODY ("|"CONDITION_BODY)* ")" // e.g. "(LOC#1#0=237)" but als (LOC#1#0=237|FOO#2#3=BAR)
CONDITION_BODY: SEGMENT_KEY "#" INT "#"INT "!"?"=" VALUE_POOL_ENTRY // "LOC#1#0=237"
SEGMENT_KEY: /[A-Z]{3,}/ // e.g. "NAD"
MULTIPLE_DATA_ELEMENTS: COMPOSITE_CHAIN ("+" COMPOSITE_CHAIN)* // e.g. "C*Can3+C*Can17*Can256"
COMPOSITE_CHAIN: COMPOSITE ("*" COMPOSITE)* // e.g. "C*Ran3{IC}"
COMPOSITE: OBLIG_MARK [CHARACTER_SET [COMPOSITE_LENGTH [VALUE_POOL]]] // e.g. "Ran3{IC}" but also plain "M"
VALUE_POOL: "{" VALUE_POOL_ENTRY("." VALUE_POOL_ENTRY)*  "}" // e.g. "{EM.FX.TE.AJ.AL}"
VALUE_POOL_ENTRY: /[A-Za-z\d\-_]+/ // e.g. "E01" // lower case and "-" for "Gabi-RLMoT" or "H2_ENGY"
COMPOSITE_LENGTH: INT // e.g. 35
CHARACTER_SET: "an"|"nn"|"np"|"aa"
OBLIG_MARK: "M"|"R"|"N"|"C"|"D"|"O" // see issue 11
ROOT_NODE: "/"
SEGMENT_GROUP_KEY: "SG" INT|"UNH"|"UNB" // e.g. "SG12"
%import common.INT
%import common.WS
%ignore WS  // WS = whitespace
"""
_parser = Lark(GRAMMAR)


def read_tree(tree: Union[str, Path]) -> Tree:
    """
    tries to parse the given tree using our .tree grammar.
    :param tree: string with the .tree content or the path to the tree file
    :return: a parsed tree
    """
    tree_str: str
    if isinstance(tree, Path):
        with open(tree, "r", encoding="utf-8") as tree_file:
            tree_str = tree_file.read()
    elif isinstance(tree, str):
        tree_str = tree
    else:
        raise ValueError(f"The provided argument is neither a path nor a str but a {tree.__class__}")
    parsed_tree = _parser.parse(tree_str)
    return parsed_tree


# todo: This parsed tree is not useful yet, but it's the basis for any future analysis/extraction.


def check_file_can_be_parsed_as_tree(file_path: Path) -> None:
    """
    Returns nothing iff the given file is parsable as .tree and contains no obvious errors.
    In case of error an exception is raised.
    """
    _ = read_tree(file_path)


def check_youngest_tree_is_parseable(dir_path: Path) -> None:
    """
    applies check_file_can_be_parsed_as_tree to the latest .tree file in the given directory
    :param dir_path:
    :return: nothing
    """
    if not dir_path.exists():
        return
    if not dir_path.is_dir():
        raise ValueError(f"You must only provide a directory path to this function but '{dir_path}' is not")
    tree_files_in_directory = sorted(dir_path.glob("*.tree"), reverse=True)
    if len(tree_files_in_directory) == 0:
        return
    relevant_file_to_check = first(tree_files_in_directory)
    check_file_can_be_parsed_as_tree(relevant_file_to_check)
