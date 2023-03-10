import os
import time
import yaml
import torch
import argparse
from tqdm import tqdm
from plot import plot_images, plot_labels
from anchor import check_anchors
from dataset import build_labels, LoadDataset
from yolo5 import YOLO5


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label_file', type=str, default='../bdd100k/labels/%s.txt')
    parser.add_argument('--image_dir', type=str, default='../bdd100k/images/%s')
    parser.add_argument('--lane_dir', type=str, default='../bdd100k/lane/masks/%s')
    parser.add_argument('--drivable_dir', type=str, default='../bdd100k/drivable/masks/%s')
    parser.add_argument('--lane_type', type=str, default='category')
    parser.add_argument('--data_file', type=str, default='../config/bdd100k.yaml')
    parser.add_argument('--hyp_file', type=str, default='../config/hyp.yaml')
    parser.add_argument('--log_dir', type=str, default='../log_dir/train')
    parser.add_argument('--pretrain_dir', type=str, default='')

    return parser.parse_args()


def train():
    pass


def main():
    # 加载数据集
    dataset = LoadDataset(opt.image_dir % ('train'), opt.lane_dir % ('train'), opt.drivable_dir % ('train'),
                          opt.lane_type, opt.yolo_label_file % ('train'), cfg)

    loader = torch.utils.data.DataLoader(dataset, batch_size=4, num_workers=1,
                                         shuffle=True, collate_fn=LoadDataset.collate_fn)

    # 选择设备
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

    log_dir = ''
    if opt.pretrain_dir == '':
        log_dir = opt.train_dir + '/' + time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
        os.makedirs(log_dir + '/weights')
        os.makedirs(log_dir + '/imgs')

        plot_labels(dataset.labels, cfg['obj'], log_dir + '/label.jpg')

        model = YOLO5(cfg['anchors'], cfg['strides'], len(cfg['target']), device, True)
        check_anchors(dataset, model, max(cfg['shape']), cfg['box_t'], cfg['bps_t'], cfg['anchor_t'],
                      cfg['iter'], cfg['gen'], cfg['mp'], cfg['sigma'], log_dir + '/anchor.txt')

    else:
        log_dir = opt.pretrain_dir

    pbar = tqdm(loader, ncols=100, desc="Epoch {}".format(1))
    for index, (imgs, lanes, drivables, labels) in enumerate(pbar):
        # print(index, imgs.shape, lanes.shape, drivables.shape, labels.shape)
        plot_images(imgs, lanes, drivables, opt.lane_type, labels, log_dir + '/imgs/' + str(index) + '.jpg')


if __name__ == "__main__":
    # 配置信息
    opt = parse_opt()
    cfg = yaml.safe_load(open(opt.data_file, encoding="utf-8"))
    hyp = yaml.safe_load(open(opt.hyp_file, encoding="utf-8"))

    # 生成标签
    if not os.path.exists(opt.label_file % 'train') or not os.path.exists(opt.label_file % 'val'):
        print('build yolo labels')

        build_labels((opt.label_file % ('train')).replace('txt', 'json'),
                     opt.label_file % ('train'), opt.image_dir % ('train'), cfg['obj'])
        build_labels((opt.label_file % ('val')).replace('txt', 'json'),
                     opt.label_file % ('val'), opt.image_dir % ('val'), cfg['obj'])


