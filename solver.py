#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sip

sip.setapi('QDate', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QString', 2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime', 2)
sip.setapi('QUrl', 2)
sip.setapi('QVariant', 2)

from PyQt4 import QtGui

import time
import sys
import operator

from components import sorted_collection
from components import gui

# ---- CONSTANTS -----
Fi_1_COST = 1
Fi_2_COST = 1
Fi_3_COST = 1
Fi_4_COST = 1
# ---
Fi_1_name = 1
Fi_2_name = 2
Fi_3_name = 3
Fi_4_name = 4
MOVES = {0: u"INIT", 1: u"▮▮_→", 2: u"▮▮_↓", 3: u"←_▮▮", 4: u"▮▮_↑"}            # readable representation of move id
SPACER = 0
manhattan_helper = {1: (0, 0), 2: (0, 1), 3: (0, 2), 4: (0, 3),
                    5: (1, 0), 6: (1, 1), 7: (1, 2), 8: (1, 3),
                    9: (2, 0), 10: (2, 1), 11: (2, 2), 12: (2, 3),
                    13: (3, 0), 14: (3, 1), 15: (3, 2), 0: (3, 3)}              # ONLY FOR 4x4 !


class Node():

    def __init__(self, parent, data, used_operation, g_func=0, h_func=0):
        self.childs = None
        self.parent = parent
        self.data = data
        self.id_ = str(data[0] + data[1] + data[2] + data[3]).replace(" ", "")     # from 2D make 1D array -> toString()
        self.g_func = g_func
        self.h_func = h_func
        self.f_func = g_func + h_func
        self.used_operation = used_operation                        # which operation (operation id) leaded to this node

    def get_child(self):
        """
        Always returns next child, or raises StopIteration exception.
        Python generator. Acts like iterator.
        """
        for leaf in self.childs:
            yield leaf

    def has_any_child(self):
        return self.childs is not None

    def print_whole_node(self, last_expanded, indent=u'|'):
        """
        Recursively prints whole node subtree or whole tree for head_node.
        Last expanded node is marked with different indent char.
        :param last_expanded: last expanded node
        :param indent: indent character
        """
        if last_expanded is self:
            indent = indent.replace(u"|", u">")

        # print current node
        print indent, unicode(self)

        # prints node childs (descendants) -> leads to recursion
        indent += u"|"
        if self.childs is not None:
            for descendant in self.get_child():
                descendant.print_whole_node(last_expanded=last_expanded, indent=indent)

    def __str__(self):
        """
        Custom class string representation.
        """
        output = u"id: %s || g_func: %s || hfunc: %s || f_func: %s || data: %s || used_operation: %s" % \
                 (self.id_, self.g_func, self.h_func, self.f_func, self.data, MOVES[self.used_operation])
        return output

    def __eq__(self, other_id):
        """
        When comparing two nodes, only their id is important.
        Much faster than compare raw data ('data' field).
        """
        return self.id_ == other_id

    def __ne__(self, other):
        return not self.__eq__(other)


def find_in_OPEN_set(id_):
    """
    :type id_: str
    :rtype: Node
    """
    try:
        found_node = OPENED[id_]
    except KeyError:
        return None
    else:
        return found_node


def find_in_CLOSED_set(id_):
    """
    :type id_: str
    :rtype: Node
    """
    try:
        found_node = CLOSED[id_]
    except KeyError:
        return None
    else:
        return found_node


def equals_with_branch_ancestors(node, new_node_id):
    """
    Searches through all ancestors and compares data (ids)
    :type node: Node
    :rtype: list of Node
    """
    # node = node.prev
    while node is not None:
        if node.id_ == new_node_id:
            return True

        node = node.parent

    return False


def remove_node_and_all_descendants(node, top_node=False):
    """
    Removes all descendants of the node from OPENED and CLOSED list.
    TOP NODE is the node which is on top of removing, basically 'on top of the tree'.
    :type node: Node
    :type top_node: bool
    """
    to_remove_from_f_func_list = []

    # IF node is a leaf ?
    if not node.has_any_child():
        # because top node is being processed differently
        if not top_node:
            node.parent = None              # delete reference so object could be released from memory
            # try to delete from OPENED or CLOSED set
            try:
                del OPENED[node.id_]
            except KeyError:
                try:
                    del CLOSED[node.id_]
                except KeyError:
                    raise Exception("Node %s is not in OPENED neither in CLOSED!" % node.id_)
            else:
                # node was found in OPENED set so it must be also deleted from f_func_list
                to_remove_from_f_func_list.append(node.id_)

            return to_remove_from_f_func_list

    # ok, so node has some other descendants -> process them => leads to recursion
    else:
        for child in node.get_child():
            to_remove_from_f_func_list.extend(remove_node_and_all_descendants(child))
        node.next = None                # delete reference so object could be released from memory

    # --------------------------------------------------------------------------------------------------
    # remove top_node itself from OPENED, CLOSED and parent.next list
    # also all removed nodes from OPENED set must be removed from f_func_list !!!
    if top_node:
        # delete from OPENED or CLOSED set
        try:
            del OPENED[node.id_]
        except KeyError:
            try:
                del CLOSED[node.id_]
            except KeyError:
                raise Exception("Node %s is not in OPENED neither in CLOSED!" % node.id_)
        else:
            # node was found in OPENED set so it must be also deleted from f_func_list
            to_remove_from_f_func_list.append(node.id_)

        # remove all already removed nodes from OPENED set also from f_func_list
        idx = 0
        len_f_func_list = len(f_func_list)
        while idx < len_f_func_list:
            if not to_remove_from_f_func_list:
                break

            f_func, id_ = f_func_list[idx]

            try:
                # same meaning as:  if node_id in to_remove_from_f_func_list then getIndexInList(node_id)
                remove_index = to_remove_from_f_func_list.index(id_)
            except ValueError:
                # if exception has been risen, it means that this node_id won't be removed from f_func_list
                idx += 1
            else:
                assert f_func_list[idx][1] == to_remove_from_f_func_list[remove_index]          # todo: sanity test - remove
                # the node_id is planned to be removed, so do it
                del f_func_list[idx]
                del to_remove_from_f_func_list[remove_index]
                len_f_func_list -= 1                                # watch out! -- we have removed item from list !

        node.parent.childs.remove(node)
        node.parent = None               # delete reference so object could be released from memory

    else:
        return to_remove_from_f_func_list


def calc_hfunc_positions(data):
    """
    Returns how many values are on their places.
    :type data: (list, list, list, list)
    :rtype: int
    """
    h = 0
    for ii in range(nrows):
        for jj in range(ncols):
            if data[ii][jj] != target_data[ii][jj]:
                h += 1

    return h                                    # - 1 if h != 0 else 0  # count only numbers, not SPACER


def calc_hfunc_manhattan(data):
    """
    Returns sum of how many steps takes move each number to its correct position. But skips SPACER position.
    Method calculate the so-called manhattan distance (city block distance)
    :type data: (list, list, list, list)
    :rtype: int
    """
    h = 0
    for ii in range(nrows):
        for jj in range(ncols):
            num = data[ii][jj]                      # number in 'data' matrix
            if num != SPACER:
                num1 = (ii, jj)                     # coordinates where number from 'data' is
                num2 = manhattan_helper[num]        # coordinates where should number from 'data' matrix be
                h += abs(num1[0] - num2[0]) + (abs(num1[1] - num2[1]))      # from its correct position
    return h


def calc_hfunc_none(data):
    """
    :type data: (list, list, list, list)
    :rtype: int
    """
    return 0


def find_spacer(data):
    """
    Returns SPACER coordinates in data array.
    :type data: list
    :return: (int, int)
    """
    for ii in range(nrows):
        for jj in range(ncols):
            if data[ii][jj] == SPACER:
                return ii, jj

    raise Exception("ERROR. SPACER not found in %s" % data)


def Fi_1_expand(data, previously_used):
    """
    Moves SPACER one box to the right ...  ▮▮→
    :type data: (list, list, list, list)
    :rtype: list, int, int
    """
    # check for complementary operation
    if previously_used == 3:
        return False

    row, col = find_spacer(data)
    swap_row, swap_col = row, col+1

    # check if indexes are in correct range, else return False (operation not permitted)
    # make a copy or node.data (from expanded node) will be changed!!!
    if (0 <= swap_row < nrows) and (0 <= swap_col < ncols):
        data = (data[0][:], data[1][:], data[2][:], data[3][:])                         # array copy (ugly but fastest)
        data[row][col], data[swap_row][swap_col] = data[swap_row][swap_col], data[row][col]     # swap values
        return data, Fi_1_name, Fi_1_COST

    return False


def Fi_2_expand(data, previously_used):
    """
    Moves SPACER one box down ...  ▮▮
                                   ↓
    :type data: (list, list, list, list)
    :rtype: list, int, int
    """
    if previously_used == 4:
        return False

    row, col = find_spacer(data)
    swap_row, swap_col = row+1, col

    # check if indexes are in correct range, else return False (operation not permitted)
    # make a copy or node.data (from expanded node) will be changed!!!
    if (0 <= swap_row < nrows) and (0 <= swap_col < ncols):
        data = (data[0][:], data[1][:], data[2][:], data[3][:])                         # array copy (ugly but fastest)
        data[row][col], data[swap_row][swap_col] = data[swap_row][swap_col], data[row][col]     # swap values
        return data, Fi_2_name, Fi_2_COST

    return False


def Fi_3_expand(data, previously_used):
    """
    Moves SPACER one box to the left ... ←▮▮
    :type data: (list, list, list, list)
    :rtype: list, int, int
    """
    if previously_used == 1:
        return False

    row, col = find_spacer(data)
    swap_row, swap_col = row, col-1

    # check if indexes are in correct range, else return False (operation not permitted)
    # make a copy or node.data (from expanded node) will be changed!!!
    if (0 <= swap_row < nrows) and (0 <= swap_col < ncols):
        data = (data[0][:], data[1][:], data[2][:], data[3][:])                         # array copy (ugly but fastest)
        data[row][col], data[swap_row][swap_col] = data[swap_row][swap_col], data[row][col]     # swap values
        return data, Fi_3_name, Fi_3_COST

    return False


def Fi_4_expand(data, previously_used):
    """
    Moves SPACER one box up ... ↑
                                ▮▮
    :type data: (list, list, list, list)
    :rtype: list, int, int
    """
    if previously_used == 2:
        return False

    row, col = find_spacer(data)
    swap_row, swap_col = row-1, col

    # check if indexes are in correct range, else return False (operation not permitted)
    # make a copy or node.data (from expanded node) will be changed!!!
    if (0 <= swap_row < nrows) and (0 <= swap_col < ncols):
        data = (data[0][:], data[1][:], data[2][:], data[3][:])                         # array copy (ugly but fastest)
        data[row][col], data[swap_row][swap_col] = data[swap_row][swap_col], data[row][col]     # swap values
        return data, Fi_4_name, Fi_4_COST

    return False


def print_output_and_return_all_moves():
    """
    When solving loop ends, method recursively digs out solution (sequence of moves).
    Each move is printed out in readable representation.
    """
    if matching_node is None:
        print "\n", "OPENED is EMPTY, solution not found!"
        return

    j = 0
    steps = []
    current_node = matching_node
    while current_node.parent is not None:          # recursively digs out path that leads to the solution
        j += 1
        steps.append(current_node.used_operation)
        current_node = current_node.parent

    print "\n\n" + "-" * 100
    steps.reverse()             # because of recursive way to get steps/moves, moves are in reversed order
    for step in steps:
        print MOVES[step] + " ",
    print "\n", "-" * 100
    print "\nThe number of moves:", \

    return steps


def check_array_dim():
    assert len(init_array) == len(target_data)
    assert len(init_array[0]) == len(target_data[0])
    assert len(init_array[1]) == len(target_data[1])
    assert len(init_array[2]) == len(target_data[2])
    assert len(init_array[3]) == len(target_data[3])


def print_selected_hfunc():
    """
    Only prints out which h_func has been selected.
    """
    if calc_hfunc is calc_hfunc_positions:
        print "H function: position"
    elif calc_hfunc is calc_hfunc_manhattan:
        print "H function: manhattan"
    elif calc_hfunc is calc_hfunc_none:
        print "H function: None"

    print "="*100


def solve_puzzle():
    matching_node = Node
    match_found = False
    iteration = 0

    # check is init state is target
    if head_node.id_ == target_node.id_:
        matching_node = head_node
        match_found = True

    while OPENED and not match_found:
        iteration += 1

        # get node with lowest f_func
        lowest_f_func, work_node_id = f_func_list[0]                # f_func_list is always sorted array
        del f_func_list[0]
        work_node = OPENED[work_node_id]
        del OPENED[work_node.id_]                                   # pop from OPENED set
        CLOSED[work_node.id_] = work_node                           # and push to CLOSED set

        # perform all expand operations on Node
        new_nodes = []
        for expand_operation in operations:
            expanded_tuple = expand_operation(work_node.data, work_node.used_operation)
            if not expanded_tuple:
                continue                                    # operation was forbidden

            # create new node from expanded data
            new_data, oper_name, oper_cost = expanded_tuple
            new_g_func = work_node.g_func + oper_cost
            new_node = Node(parent=work_node, data=new_data, g_func=new_g_func,
                            h_func=calc_hfunc(new_data), used_operation=oper_name)

            # is this target node?
            if new_node.id_ == target_node.id_:
                matching_node = new_node
                match_found = True
                break

            if equals_with_branch_ancestors(work_node, new_node.id_):
                continue

            # find if new node has been already opened (closed) in past
            found_in_OPENED = find_in_OPEN_set(new_node.id_)
            if found_in_OPENED:
                if found_in_OPENED.g_func > new_g_func:
                    remove_node_and_all_descendants(found_in_OPENED, top_node=True)
                else:
                    continue        # already expaneded is better
            else:
                found_in_CLOSED = find_in_CLOSED_set(new_node.id_)
                if found_in_CLOSED:
                    if found_in_CLOSED.g_func > new_g_func:
                        remove_node_and_all_descendants(found_in_CLOSED, top_node=True)
                    else:
                        continue    # already expaneded is better

            # add to OPENED set
            OPENED[new_node.id_] = new_node
            f_func_list.insert_right( (new_node.f_func, new_node.id_) )
            new_nodes.append(new_node)      # will be added to OPENED list

        last_expanded = work_node
        work_node.childs = new_nodes if new_nodes else None

        sys.stdout.write('\riteration: %s, h_func: %s' % (iteration, work_node.h_func))
        sys.stdout.flush()          # important

    # update last time
    sys.stdout.write('\riteration: %s, h_func: %s' % (iteration, matching_node.h_func))
    sys.stdout.flush()          # important

    return matching_node, iteration


if __name__ == "__main__":
    # ===============================================================================================================

    # ----   IMPORTANT - SELECT only one   ------
    # calc_hfunc = calc_hfunc_positions
    calc_hfunc = calc_hfunc_manhattan
    # calc_hfunc = calc_hfunc_none
    # -------------------------------------------

    # simple
    init_array = ([SPACER, 2, 3, 4], [6, 5, 10, 12], [9, 1, 8, 15], [13, 14, 7, 11])
    # init_array = ([SPACER, 6, 2, 3], [5, 10, 8, 4], [9, 1, 7, 12], [13, 14, 11, 15])
    # init_array = ([SPACER, 1, 2, 3], [5, 6, 8, 4], [9, 10, 7, 12], [13, 14, 11, 15])
    # hardcore
    # init_array = ([SPACER, 2, 12, 6], [9, 7, 14, 13], [5, 4, 1, 11], [3, 15, 10, 8])
    target_data = ([1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, SPACER])

    # ============================================SOLVER============================================================

    check_array_dim()
    print_selected_hfunc()

    # solver init
    t0 = time.time()
    nrows, ncols = len(target_data), len(target_data[0])
    operations = (Fi_1_expand, Fi_2_expand, Fi_3_expand, Fi_4_expand)

    # node init
    head_node = Node(parent=None, data=init_array, g_func=0, h_func=calc_hfunc(init_array), used_operation=0)
    target_node = Node(parent=None, data=target_data, g_func=0, h_func=0, used_operation=0)

    # working sets init
    OPENED = {head_node.id_: head_node}
    CLOSED = {}
    f_func_list = sorted_collection.SortedCollection(key=operator.itemgetter(0))
    f_func_list.insert_right( (head_node.f_func, head_node.id_) )

    # SOLVE PUZZLE
    matching_node, iteration = solve_puzzle()
    solving_steps = print_output_and_return_all_moves()

    print u"The number of iterations:", iteration
    print u"Total time consumed: %ss" % (time.time() - t0)

    # ===============================================GUI=============================================================

    # app = QtGui.QApplication(sys.argv)
    # app.setApplicationName(u"'15' puzzle solver")
    # main = gui.MainWindow(nrows, ncols, init_array, SPACER, solving_steps)
    # main.show()
    # app.exec_()




