# Import
import math

# Definitions

def get_closest_number(my_list, my_number):
    new_list = []
    for i in my_list:
        new_list.append(i - my_number)
    abs_list = [abs(ele) for ele in new_list]
    index = abs_list.index(min(abs_list))
    value = my_list[index]
    if value - my_number <= 0:
        try:
            value = my_list[index + 1]
        except IndexError:
            pass
    return value

def roundup(x, base=5):
    return base * math.ceil(x / base)