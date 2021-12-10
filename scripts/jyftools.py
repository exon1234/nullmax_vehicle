import os
import numpy as np
import pandas as pd
from collections import defaultdict
import time


def compute_IoU_IoS(df):
    """compute IoU and IoS between ground-truth bboxes and detected bboxes"""
    arr_gt = df[['cx_gt', 'cy_gt', 'w_gt', 'h_gt']].values
    arr_det = df[['cx_det', 'cy_det', 'w_det', 'h_det']].values

    corners_gt = np.zeros_like(arr_gt)
    corners_gt[:, 0] = arr_gt[:, 0] - arr_gt[:, 2] / 2
    corners_gt[:, 1] = arr_gt[:, 1] - arr_gt[:, 3] / 2
    corners_gt[:, 2] = arr_gt[:, 0] + arr_gt[:, 2] / 2
    corners_gt[:, 3] = arr_gt[:, 1] + arr_gt[:, 3] / 2

    corners_det = np.zeros_like(arr_det)
    corners_det[:, 0] = arr_det[:, 0] - arr_det[:, 2] / 2
    corners_det[:, 1] = arr_det[:, 1] - arr_det[:, 3] / 2
    corners_det[:, 2] = arr_det[:, 0] + arr_det[:, 2] / 2
    corners_det[:, 3] = arr_det[:, 1] + arr_det[:, 3] / 2

    insec = np.zeros_like(arr_gt)
    insec[:, 0] = np.maximum(corners_gt[:, 0], corners_det[:, 0])
    insec[:, 1] = np.maximum(corners_gt[:, 1], corners_det[:, 1])
    insec[:, 2] = np.minimum(corners_gt[:, 2], corners_det[:, 2])
    insec[:, 3] = np.minimum(corners_gt[:, 3], corners_det[:, 3])

    area_gt = df['area_gt'].values
    area_det = df['area_det'].values

    insec_area = np.maximum(0, insec[:, 2] - insec[:, 0]) * np.maximum(0, insec[:, 3] - insec[:, 1])
    ios_gt = np.round(np.where(np.isnan(area_gt) | np.isnan(area_det), -1, insec_area / area_gt), 6)
    ios_det = np.round(np.where(np.isnan(area_gt) | np.isnan(area_det), -1, insec_area / area_det), 6)
    iou = np.round(np.where(np.isnan(area_gt) | np.isnan(area_det), -1, insec_area / (area_gt + area_det - insec_area)),
                   6)
    return ios_gt.reshape(-1, 1), ios_det.reshape(-1, 1), iou.reshape(-1, 1)
    # return np.hstack([ios_gt.reshape(-1, 1), ios_det.reshape(-1, 1), iou.reshape(-1, 1)])


def compute_IoU(bbox1, bbox2):
    arr_gt = bbox1[['cx', 'cy', 'w', 'h']].values
    arr_det = bbox2[['cx', 'cy', 'w', 'h']].values

    corners_gt = np.zeros_like(arr_gt)
    corners_gt[:, 0] = arr_gt[:, 0] - arr_gt[:, 2] / 2
    corners_gt[:, 1] = arr_gt[:, 1] - arr_gt[:, 3] / 2
    corners_gt[:, 2] = arr_gt[:, 0] + arr_gt[:, 2] / 2
    corners_gt[:, 3] = arr_gt[:, 1] + arr_gt[:, 3] / 2

    corners_det = np.zeros_like(arr_det)
    corners_det[:, 0] = arr_det[:, 0] - arr_det[:, 2] / 2
    corners_det[:, 1] = arr_det[:, 1] - arr_det[:, 3] / 2
    corners_det[:, 2] = arr_det[:, 0] + arr_det[:, 2] / 2
    corners_det[:, 3] = arr_det[:, 1] + arr_det[:, 3] / 2

    insec = np.zeros_like(arr_gt)
    insec[:, 0] = np.maximum(corners_gt[:, 0], corners_det[:, 0])
    insec[:, 1] = np.maximum(corners_gt[:, 1], corners_det[:, 1])
    insec[:, 2] = np.minimum(corners_gt[:, 2], corners_det[:, 2])
    insec[:, 3] = np.minimum(corners_gt[:, 3], corners_det[:, 3])

    area_gt = bbox1['area'].values
    area_det = bbox2['area'].values

    insec_area = np.maximum(0, insec[:, 2] - insec[:, 0]) * np.maximum(0, insec[:, 3] - insec[:, 1])
    iou = np.round(np.where(np.isnan(area_gt) | np.isnan(area_det), -1, insec_area / (area_gt + area_det - insec_area)),
                   6)
    return iou.reshape(-1)


def evaluate_img(c_gts, c_dets, c_ious, cfgs, imgId, catId, aRng, maxDet):
    '''
    perform evaluation for single category and image
    :return: dict (single image results)
    '''
    gt = c_gts[imgId, catId]
    dt = c_dets[imgId, catId]

    if len(gt) == 0 and len(dt) == 0:
        return None

    for g in gt:
        if g['area'] < aRng[0] or g['area'] > aRng[1]:
            g['_ignore'] = 1
        else:
            g['_ignore'] = 0

    # sort dt highest score first, sort gt ignore last
    gtind = np.argsort([g['_ignore'] for g in gt], kind='mergesort')
    gt = [gt[i] for i in gtind]
    dtind = np.argsort([-d['score'] for d in dt], kind='mergesort')
    dt = [dt[i] for i in dtind[0:maxDet]]
    # load computed ious
    ious = c_ious[imgId, catId]

    assert (len(gt) * len(dt) == len(ious))
    T = len(cfgs['iou_thres'])
    G = len(gt)
    D = len(dt)
    gtm = np.zeros((T, G))
    dtm = np.zeros((T, D))
    gtIg = np.array([g['_ignore'] for g in gt])
    dtIg = np.zeros((T, D))
    if not len(ious) == 0:
        for tind, t in enumerate(cfgs['iou_thres']):
            for dind, d in enumerate(dt):
                # information about best match so far (m=-1 -> unmatched)
                iou = min([t, 1 - 1e-10])
                m = -1
                for gind, g in enumerate(gt):
                    # if g['id'] != d['id']:
                    #     continue
                    # if this gt already matched, and not a crowd, continue
                    if gtm[tind, gind] != 0:
                        continue
                    # if dt matched to reg gt, and on ignore gt, stop
                    if m > -1 and gtIg[m] == 0 and gtIg[gind] == 1:
                        break
                    # continue to next gt unless better match made
                    # if ious[dind,gind] < iou:
                    if ious[d['id'], g['id']] < iou:
                        continue
                    # if match successful and best so far, store appropriately
                    # iou=ious[dind,gind]
                    iou = ious[d['id'], g['id']]
                    m = gind
                # if match made store id of match for both dt and gt
                if m == -1:
                    continue
                dtIg[tind, dind] = gtIg[m]
                dtm[tind, dind] = gt[m]['id']
                gtm[tind, m] = d['id']
    # set unmatched detections outside of area range to ignore
    a = np.array([d['area'] < aRng[0] or d['area'] > aRng[1] for d in dt]).reshape((1, len(dt)))
    dtIg = np.logical_or(dtIg, np.logical_and(dtm == 0, np.repeat(a, T, 0)))
    # store results for given image and category
    return {
        'image_id': imgId,
        'category_id': catId,
        'aRng': aRng,
        'maxDet': maxDet,
        'dtIds': [d['id'] for d in dt],
        'gtIds': [g['id'] for g in gt],
        'dtMatches': dtm,
        'gtMatches': gtm,
        'dtScores': [d['score'] for d in dt],
        'gtIgnore': gtIg,
        'dtIgnore': dtIg,
    }


def accumulate(cfgs, imgids, eval_imgs_res):
    '''
    Accumulate per image evaluation results and store the result in self.eval
    :param p: input params for evaluation
    :return: None
    '''
    stime = time.time()
    print('==> Accumulating evaluation results...')
    T = len(cfgs['iou_thres'])
    R = len(cfgs['recall_thres'])
    K = len(cfgs['catenms'])
    A = len(cfgs['area_ranges'])
    M = len(cfgs['max_dets'])
    precision = -np.ones((T, R, K, A, M))  # -1 for the precision of absent categories
    recall = -np.ones((T, K, A, M))
    scores = -np.ones((T, R, K, A, M))

    # create dictionary for future indexing
    setK = set(cfgs['catenms'])
    setA = set(map(tuple, cfgs['area_ranges']))
    setM = set(cfgs['max_dets'])
    setI = set(imgids)
    # get inds to evaluate
    k_list = [n for n, k in enumerate(cfgs['catenms']) if k in setK]
    a_list = [n for n, a in enumerate(map(lambda x: tuple(x), cfgs['area_ranges'])) if a in setA]
    m_list = [m for n, m in enumerate(cfgs['max_dets']) if m in setM]
    i_list = [n for n, i in enumerate(imgids) if i in setI]
    I0 = len(imgids)
    A0 = len(cfgs['area_ranges'])
    # retrieve E at each category, area range, and max number of detections
    for k, k0 in enumerate(k_list):
        Nk = k0 * A0 * I0
        for a, a0 in enumerate(a_list):
            Na = a0 * I0
            for m, maxDet in enumerate(m_list):
                # print(len(self.eval_imgs_res), [Nk + Na + i for i in i_list])
                E = [eval_imgs_res[Nk + Na + i] for i in i_list]
                E = [e for e in E if not e is None]

                if len(E) == 0:
                    continue
                dtScores = np.concatenate([e['dtScores'][0:maxDet] for e in E])

                # different sorting method generates slightly different results.
                # mergesort is used to be consistent as Matlab implementation.
                inds = np.argsort(-dtScores, kind='mergesort')
                dtScoresSorted = dtScores[inds]

                dtm = np.concatenate([e['dtMatches'][:, 0:maxDet] for e in E], axis=1)[:, inds]
                dtIg = np.concatenate([e['dtIgnore'][:, 0:maxDet] for e in E], axis=1)[:, inds]
                gtIg = np.concatenate([e['gtIgnore'] for e in E])
                npig = np.count_nonzero(gtIg == 0)
                if npig == 0:
                    continue
                tps = np.logical_and(dtm != 0, np.logical_not(dtIg))
                fps = np.logical_and(np.logical_not(dtm != 0), np.logical_not(dtIg))

                tp_sum = np.cumsum(tps, axis=1).astype(dtype=np.float)
                fp_sum = np.cumsum(fps, axis=1).astype(dtype=np.float)

                for t, (tp, fp) in enumerate(zip(tp_sum, fp_sum)):
                    tp = np.array(tp)
                    fp = np.array(fp)
                    nd = len(tp)
                    rc = tp / npig
                    pr = tp / (fp + tp + np.spacing(1))
                    q = np.zeros((R,))
                    ss = np.zeros((R,))
                    # if (k==0) and (a==0) and (m==2) and (t==0):
                    #     print('total_gt:', npig)
                    #     print(pr)
                    #     print(rc)
                    #     print('********')
                    if nd:
                        recall[t, k, a, m] = rc[-1]
                    else:
                        recall[t, k, a, m] = 0

                    # numpy is slow without cython optimization for accessing elements
                    # use python array gets significant speed improvement
                    pr = pr;
                    q = q

                    for i in range(nd - 1, 0, -1):
                        if pr[i] > pr[i - 1]:
                            pr[i - 1] = pr[i]

                    inds = np.searchsorted(rc, cfgs['recall_thres'], side='left')
                    try:
                        for ri, pi in enumerate(inds):
                            q[ri] = pr[pi]
                            ss[ri] = dtScoresSorted[pi]
                    except:
                        pass
                    precision[t, :, k, a, m] = np.array(q)
                    scores[t, :, k, a, m] = np.array(ss)
    c_eval = {
        'counts': [T, R, K, A, M],
        'precision': precision,
        'recall': recall,
        'scores': scores,
    }
    print('    accumulate time(s): {:.2}'.format(time.time() - stime))
    return c_eval


def summarize(cfgs, c_eval):
    '''
    Compute and display summary metrics for evaluation results.
    Note this functin can *only* be applied on the default parameter setting
    '''

    def _summarize(ap=1, catenm='all', iouThr=None, areaRng='all', maxDets=100):
        iStr = ' {:<18} {} @[ IoU={:<9} | catenm={:<10s} | area={:>6s} | maxDets={:>3d} ] = {:0.3f}'
        titleStr = 'Average Precision' if ap == 1 else 'Average Recall'
        typeStr = '(AP)' if ap == 1 else '(AR)'
        iouStr = '{:0.2f}:{:0.2f}'.format(cfgs['iou_thres'][0], cfgs['iou_thres'][-1]) \
            if iouThr is None else '{:0.2f}'.format(iouThr)

        aind = [i for i, aRng in enumerate(cfgs['area_types']) if aRng == areaRng]
        mind = [i for i, mDet in enumerate(cfgs['max_dets']) if mDet == maxDets]
        kind = [i for i, kCatnm in enumerate(cfgs['catenms']) if kCatnm == catenm]

        if ap == 1:
            # dimension of precision: [TxRxKxAxM]
            s = c_eval['precision']
            # IoU
            if iouThr is not None:
                t = np.where(iouThr == cfgs['iou_thres'])[0]
                s = s[t]
            if catenm == 'all':
                s = s[:, :, :, aind, mind]
            else:
                s = s[:, :, kind, aind, mind]
        else:
            # dimension of recall: [TxKxAxM]
            s = c_eval['recall']
            if iouThr is not None:
                t = np.where(iouThr == cfgs['iou_thres'])[0]
                s = s[t]
            if catenm == 'all':
                s = s[:, :, aind, mind]
            else:
                s = s[:, kind, aind, mind]
        if len(s[s > -1]) == 0:
            mean_s = -1
        else:
            mean_s = np.mean(s[s > -1])
        if catenm == 'all':
            print(iStr.format(titleStr, typeStr, iouStr, catenm, areaRng, maxDets, mean_s))

        return mean_s

    def _summarizeDets():
        stats_all_catenms = {}
        for catenm in ['all'] + cfgs['catenms']:
            stats = np.zeros((12,))
            stats[0] = _summarize(1, catenm=catenm)
            stats[1] = _summarize(1, catenm=catenm, iouThr=.5, maxDets=cfgs['max_dets'][2])
            stats[2] = _summarize(1, catenm=catenm, iouThr=.75, maxDets=cfgs['max_dets'][2])
            stats[3] = _summarize(1, catenm=catenm, areaRng='small', maxDets=cfgs['max_dets'][2])
            stats[4] = _summarize(1, catenm=catenm, areaRng='medium', maxDets=cfgs['max_dets'][2])
            stats[5] = _summarize(1, catenm=catenm, areaRng='large', maxDets=cfgs['max_dets'][2])

            stats[6] = _summarize(0, catenm=catenm, maxDets=cfgs['max_dets'][0])
            stats[7] = _summarize(0, catenm=catenm, maxDets=cfgs['max_dets'][1])
            stats[8] = _summarize(0, catenm=catenm, maxDets=cfgs['max_dets'][2])
            stats[9] = _summarize(0, catenm=catenm, areaRng='small', maxDets=cfgs['max_dets'][2])
            stats[10] = _summarize(0, catenm=catenm, areaRng='medium', maxDets=cfgs['max_dets'][2])
            stats[11] = _summarize(0, catenm=catenm, areaRng='large', maxDets=cfgs['max_dets'][2])
            stats_all_catenms[catenm] = stats

        return stats_all_catenms

    if not c_eval:
        raise Exception('Please run accumulate() first')

    eval_stats = _summarizeDets()
    return eval_stats


def to_excel(gts, stats, imgids, cfgs, eval_stats):
    def _map(e):
        return '{:.2f}'.format(e * 100) if isinstance(e, float) else e

    catenm_num_map = gts.groupby('catenm')['annid'].count().to_dict()
    print(catenm_num_map)
    missed_gt = stats['missed_gt'].to_dict()
    cate_miscls = stats['cate_miscls'].to_dict()
    false_det = stats['false_det'].to_dict()
    stats_dict = defaultdict(list)
    imgnums = len(imgids)
    objnums = sum(catenm_num_map.values())
    for catenm in ['all'] + ['car', 'truck', 'bus']:
        stats_dict['Category'].append(catenm)
        if catenm == 'all':
            stats_dict['FPPI(%)'].append(_map(sum(stats['false_det']) / imgnums))
            stats_dict['FNPI(%)'].append(_map(sum(stats['missed_gt']) / objnums))
            stats_dict['CEPI(%)'].append(_map(sum(stats['cate_miscls']) / objnums))
        else:
            stats_dict['FPPI(%)'].append(_map(false_det.get(catenm, 0) / imgnums))
            stats_dict['FNPI(%)'].append(_map(missed_gt.get(catenm, 0) / catenm_num_map[catenm]))
            stats_dict['CEPI(%)'].append(_map(cate_miscls.get(catenm, 0) / catenm_num_map[catenm]))
        metrics = ['AP', 'AP50', 'AP75', 'AP(S)', 'AP(M)', 'AP(L)', 'AR1', 'AR10', 'AR100', 'AR(S)', 'AR(M)', 'AR(L)']
        for ind, metric in enumerate(metrics):
            stats_dict[metric + '(%)'].append(_map(eval_stats[catenm][ind]))

    stats_df = pd.DataFrame(stats_dict)
    res_fpath = os.path.join('./test_result/jiao/mAP', 'eval_stats.xlsx')
    with pd.ExcelWriter(res_fpath) as writer:

        stats_df.to_excel(writer, sheet_name='eval')
    print('==> res saved to {}'.format(res_fpath))


def SampEn(y):
    def get_sigma(group, m, N, thresh):
        cmi = []
        for i in range(len(group)):
            count = 0
            for j in range(len(group)):
                if i == j:
                    continue
                x1 = group[i]
                x2 = group[j]
                dm = max([abs(x1[p] - x2[p]) for p in range(m)])
                if dm < thresh:
                    count += 1
            cmi.append(1.0 * count / (N - m))
        cm = sum(cmi) / (N - m + 1)
        return cm

    m = 2
    N = len(y)
    if (m + 1) > N:
        return None
    thresh = 0.25 * np.std(y, ddof=1)
    re_group_m = []
    re_group_m_plus = []
    for i in range(N - m):
        sub_group = []
        for j in range(m):
            sub_group.append(y[i + j])
        re_group_m.append(sub_group)
    for i in range(N - m - 1):
        sub_group = []
        for j in range(m + 1):
            sub_group.append(y[i + j])
        re_group_m_plus.append(sub_group)
    cm = get_sigma(re_group_m, m, N, thresh)
    cm_plus = get_sigma(re_group_m_plus, m + 1, N, thresh)
    if cm_plus == 0:
        return None
    samplEn = -np.log(cm_plus / (cm + 1e-6))
    return samplEn
