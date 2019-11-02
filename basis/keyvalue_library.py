# -*- coding: utf-8 -*-
# @Time    : 2019/11/2
# @Author  : ForestNeo
# @Site    : forestneo.com
# @Email   : dr.forestneo@gmail.com
# @File    : keyvalue_library.py
# @Software: PyCharm
# @Function: 

import numpy as np
import basis.local_differential_privacy_library as ldplib


def kvlist_get_baseline(kv_list: np.ndarray, discretization=False):
    if not isinstance(discretization, bool):
        raise Exception("type error")
    f = np.average(kv_list[:, 0])

    value_list = []
    for kv in kv_list:
        if int(kv[0]) == 1 and discretization is True:
            value_list.append(ldplib.discretization(kv[1], lower=-1, upper=1))
        elif int(kv[0]) == 1 and discretization is False:
            value_list.append(kv[1])
        else:
            pass
    m = np.average(np.asarray(value_list))
    return f, m


def kvt_get_baseline(kvt: np.ndarray, discretization=False):
    if not isinstance(kvt, np.ndarray):
        raise Exception("type error of kvt: ", type(kvt))

    n, d = kvt.shape[0], kvt.shape[1]
    f_list, m_list = np.zeros([d]), np.zeros([d])

    for i in range(d):
        kv_list = kvt[:, i]
        f, m = kvlist_get_baseline(kv_list, discretization=discretization)
        f_list[i], m_list[i] = f, m
    return f_list, m_list


def kv_en_privkv(kv, epsilon1, epsilon2, set_value=None):
    k, v = int(kv[0]), kv[1]
    if k == 1:
        k = ldplib.perturbation(value=k, perturbed_value=1-k, epsilon=epsilon1)
        if k == 1:
            discretize_v = ldplib.discretization(v, -1, 1)
            p_k, p_v = 1, ldplib.perturbation(value=discretize_v, perturbed_value=-discretize_v, epsilon=epsilon2)
        else:
            p_k, p_v = 0, 0
    else:
        k = ldplib.perturbation(value=k, perturbed_value=1 - k, epsilon=epsilon1)
        if k == 1:
            v = np.random.uniform(low=-1, high=1) if set_value is None else set_value
            discretize_v = ldplib.discretization(v, -1, 1)
            p_k, p_v = 1, ldplib.perturbation(value=discretize_v, perturbed_value=-discretize_v, epsilon=epsilon2)
        else:
            p_k, p_v = 0, 0
    return [p_k, p_v]


def kv_de_privkv(p_kv_list: np.ndarray, epsilon1, epsilon2):
    p1 = np.e**epsilon1 / (1 + np.e**epsilon1)
    p2 = np.e**epsilon2 / (1 + np.e**epsilon2)

    k_list = p_kv_list[:, 0]
    v_list = p_kv_list[:, 1]

    f = (np.average(k_list) + p1-1) / (2*p1 - 1)
    # the [0] is because np.where() returns a tuple (x,y), x is the list and y it the type of elements of the array
    n1 = len(np.where(v_list == 1)[0])
    n2 = len(np.where(v_list == -1)[0])

    N = n1 + n2
    n1_star = (p2-1) / (2*p2-1) * N + n1 / (2*p2-1)
    n2_star = (p2-1) / (2*p2-1) * N + n2 / (2*p2-1)
    n1_star = np.clip(n1_star, 0, N)
    n2_star = np.clip(n2_star, 0, N)
    m = (n1_star - n2_star) / N

    return f, m


def kv_en_state_encoding(kv, epsilon):
    """
        The unary encoding, also known as k-random response, is used in user side. It works as follows
        First, key value data is mapped into {0, 1, 2}. Basically, [0,0]->1; [1,-1]->0; [1,1]->2;
        Then the k-rr is used to report.
        :param kv: key value data, in which k in {0,1} and value in [-1,1]
        :param epsilon: privacy budget
        :return: the encoded key value data, the res is in {0,1,2}
        """
    if not isinstance(kv, np.ndarray) or len(kv) is not 2:
        print(type(kv), len(kv))
        raise Exception("type error")

    k, v = kv[0], ldplib.discretization(value=kv[1], lower=-1, upper=1)
    unary = k * v + 1
    return ldplib.k_random_response(unary, values=[0, 1, 2], epsilon=epsilon)


def kv_de_state_encoding(p_kv_list: np.ndarray, epsilon):
    """
    This is used in the server side. The server collects all the data and then use this function to calculate f and m.
    :param p_kv_list: the encoded kv list
    :param epsilon: the privacy budget
    :return: the estimated frequency and mean.
    """
    zero = len(np.where(p_kv_list == 1)[0])  # [0,0]
    pos = len(np.where(p_kv_list == 2)[0])  # [1,1]
    neg = len(np.where(p_kv_list == 0)[0])  # [1,-1]
    cnt_all = zero + pos + neg

    # adjust the true count
    cnt = np.asarray([zero, pos, neg])
    p = np.e ** epsilon / (2 + np.e ** epsilon)

    est_cnt = (2 * cnt - cnt_all * (1 - p)) / (3 * p - 1)

    f = (est_cnt[1] + est_cnt[2]) / cnt_all
    m = (est_cnt[1] - est_cnt[2]) / (est_cnt[1] + est_cnt[2])
    return f, np.clip(m, -1, 1)


def my_run_tst():
    # generate 10000 kv pairs with f=0.7 and m=0.3
    kv_list = [[np.random.binomial(1, 0.7), np.clip(a=np.random.normal(loc=0.3, scale=0.2), a_min=-1, a_max=1)] for _ in
               range(10000)]
    f, m = kvlist_get_baseline(kv_list=np.asarray(kv_list))
    print("this is the baseline f=%.4f, m=%.4f" % (f, m))


if __name__ == '__main__':
    my_run_tst()
