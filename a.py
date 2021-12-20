def replace_elements_by_list(elements_list, values_list):
    for i, e in enumerate(elements_list):
        for j, v in enumerate(lst_2):
            if e == v[0]:
                elements_list[i] = values_list[j][1]
    return elements_list


lst = [1, 2, 3, 4, 5, 6, 7]
lst_2 = [[3, "c"], [1, "a"], [2, "b"], [4, "d"], [7, "x"]]


print(replace_elements_by_list(lst, lst_2))
