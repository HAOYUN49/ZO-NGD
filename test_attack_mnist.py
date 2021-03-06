
#new file!
import tensorflow as tf
import numpy as np
import time
import random
import os
from numpy import linalg as LA

from setup_cifar import CIFAR, CIFARModel
from setup_mnist import MNIST, MNISTModel
from setup_inception import ImageNet, InceptionModel

from l2_attack import CarliniL2

from l2_blackbox_attack_second_mnist import LADMMBB

from PIL import Image


def show(img, name = "output.png"):
    fig = (img + 0.5)*255
    fig = fig.astype(np.uint8).squeeze()
    pic = Image.fromarray(fig)
    # pic.resize((512,512), resample=PIL.Image.BICUBIC)
    pic.save(name)


def generate_data(data, model, samples, targeted=True, target_num=9, start=0, inception=False, seed=3, handpick=False ):
    """
    Generate the input data to the attack algorithm.

    data: the images to attack
    samples: number of samples to use
    targeted: if true, construct targeted attacks, otherwise untargeted attacks
    start: offset into data to use
    inception: if targeted and inception, randomly sample 100 targets intead of 1000
    """
    random.seed(seed)
    inputs = []
    targets = []
    labels = []
    true_ids = []
    sample_set = []

    data_d = data.test_data
    labels_d = data.test_labels

    if handpick:
        if inception:
            deck = list(range(0, 1500))
        else:
            deck = list(range(0, 10000))
        random.shuffle(deck)
        print('Handpicking')

        while (len(sample_set) < samples):
            rand_int = deck.pop()
            pred = model.model.predict(data_d[rand_int:rand_int + 1])

            if inception:
                pred = np.reshape(pred, (labels_d[0:1].shape))

            if (np.argmax(pred, 1) == np.argmax(labels_d[rand_int:rand_int + 1], 1)):
                sample_set.append(rand_int)
        print('Handpicked')
    else:
        sample_set = random.sample(range(0, 10000), samples)

    for i in sample_set:

        if targeted:
            seq = np.random.randint(labels_d.shape[1])
            while seq == np.argmax(labels_d[start + i]):
                seq = np.random.randint(labels_d.shape[1])

            inputs.append(data_d[start + i])
            targets.append(np.eye(labels_d.shape[1])[seq]) #target labels
            labels.append(labels_d[start + i]) #correct labels
            true_ids.append(start + i)

        else:
            inputs.append(data_d[start + i])
            targets.append(labels_d[start + i]) #correct labels
            labels.append(labels_d[start + i]) #correct labels
            true_ids.append(start + i) #编号

    inputs = np.array(inputs)
    targets = np.array(targets)
    labels = np.array(labels)
    true_ids = np.array(true_ids)
    return inputs, targets, labels, true_ids


def generate_data_original(data, model, samples, targeted=True, target_num=9, start=0, inception=False, seed=3, handpick=False ):
    """
    Generate the input data to the attack algorithm.

    data: the images to attack
    samples: number of samples to use
    targeted: if true, construct targeted attacks, otherwise untargeted attacks
    start: offset into data to use
    inception: if targeted and inception, randomly sample 100 targets intead of 1000
    """
    random.seed(seed)
    inputs = []
    targets = []
    labels = []
    true_ids = []
    sample_set = []

    data_d = data.test_data
    labels_d = data.test_labels

    if handpick:
        if inception:
            deck = list(range(0, 1500))
        else:
            deck = list(range(0, 10000))
        random.shuffle(deck)
        print('Handpicking')

        while (len(sample_set) < samples):
            rand_int = deck.pop()
            pred = model.model.predict(data_d[rand_int:rand_int + 1])

            if inception:
                pred = np.reshape(pred, (labels_d[0:1].shape))

            if (np.argmax(pred, 1) == np.argmax(labels_d[rand_int:rand_int + 1], 1)):
                sample_set.append(rand_int)
        print('Handpicked')
    else:
        sample_set = random.sample(range(0, 10000), samples)

    for i in sample_set:
        if targeted:
            if inception:
                seq = random.sample(range(1, 1001), target_num)
            else:
                seq = range(labels_d.shape[1])

      #      seq = {1}
            for j in seq:
                if (j == np.argmax(labels_d[start + i])) and (inception == False):
                    continue
                inputs.append(data_d[start + i])
                targets.append(np.eye(labels_d.shape[1])[j])
                labels.append(labels_d[start + i])
                true_ids.append(start + i)
        else:
            inputs.append(data_d[start + i])
            targets.append(labels_d[start + i])
            labels.append(labels_d[start + i])
            true_ids.append(start + i)

    inputs = np.array(inputs)
    targets = np.array(targets)
    labels = np.array(labels)
    true_ids = np.array(true_ids)
    return inputs, targets, labels, true_ids

def l1_l2_li_computation(args, data, model, adv, inception, inputs, targets, labels, true_ids, querycount, queryl2):

    d_average_l2 = []
    d_average_l1 = []
    d_average_linf = []
    r_average = []
    if (args['show']):
        if not os.path.exists(str(args['save']) + "/" + str(args['dataset']) + "/" + str(args['attack']) + "/" + "targeted"):
            os.makedirs(str(args['save']) + "/" + str(args['dataset']) + "/" + str(args['attack']) + "/" + "targeted")

    for j in range(len(inputs)):
    #    pred = []
        if inception:
    #        pred.append(np.reshape(model.model.predict(adv[j:j + 1]), (data.test_labels[0:1].shape)))
            pred_r = np.reshape(model.model.predict(adv[j:j + 1]), (data.test_labels[0:1].shape))
        else:
     #       pred.append(model.model.predict(adv[j:j + 1]))
            pred_r = model.model.predict(adv[j:j + 1])

        if (np.argmax(pred_r, 1) == np.argmax(targets[j:j + 1], 1)):
            r_average.append(1)
            d_average_l2.append(np.sum((adv[j] - inputs[j]) ** 2) ** .5)
            d_average_l1.append(np.sum(np.abs(adv[j] - inputs[j])))
            d_average_linf.append(np.amax(np.abs(adv[j] - inputs[j])))
        else:
            r_average.append(0)

        if args['show']:
            target_id = np.argmax(targets[j:j+ 1], 1)
            label_id = np.argmax(labels[j:j+1], 1)
            prev_id = np.argmax(np.reshape(model.model.predict(inputs[j:j + 1]), 
                (data.test_labels[0:1].shape)), 1)
            adv_id = np.argmax(np.reshape(model.model.predict(adv[j:j + 1]), (data.test_labels[0:1].shape)), 1)
            suffix = "id{}_seq{}_lbl{}_prev{}_adv{}_{}_l1_{:.3f}_l2_{:.3f}_linf_{:.3f}".format(
                true_ids[j],
                target_id,
                label_id,
                prev_id,
                adv_id,
                adv_id == target_id,
                np.sum(np.abs(adv[j] - inputs[j])),
                np.sum((adv[j] - inputs[j]) ** 2) ** .5,
                np.amax(np.abs(adv[j] - inputs[j])))

            show(inputs[j:j + 1], str(args['save']) + "/" + str(args['dataset']) + "/" + str(
                args['attack']) + "/" + "targeted" + "/original_{}.png".format(suffix))
            show(adv[j:j + 1], str(args['save']) + "/" + str(args['dataset']) + "/" + str(
                args['attack']) + "/" + "targeted" + "/adversarial_{}.png".format(suffix))


    queryl23 = np.sqrt(queryl2) / inputs.shape[1] / inputs.shape[2] / inputs.shape[3]


    print(np.array(d_average_l2))
    print('average_L2_mean', np.mean(d_average_l2))
    print('average_L1_mean', np.mean(d_average_l1))
    print('average_Li_mean', np.mean(d_average_linf))
    print('average__prob', np.mean(r_average))

    print('smallest_query_count', np.min(querycount))
    print('mean_query_count', np.mean(querycount))
    print('largest_query_count', np.max(querycount))
    #print('smallest_query_l2_first_success', np.mean(qcl2_batch_min))
    #print('mean_query_l2_first_success', np.mean(qcl2_batch_mean))
    #print('largest_query_l2_first_success', np.mean(qcl2_batch_max))
    print(targets)


def l2_computation(args, data, model, adv, inception, inputs, targets, labels, true_ids, querycount, queryl2):
    #args, data, model, adv, inception, inputs, targets, labels, true_ids, querycount, queryl2

    d_average_l2 = []
    d_average_l1 = []
    d_average_linf = []
    r_average = []
    if (args['show']):
        if not os.path.exists(str(args['save']) + "/" + str(args['dataset']) + "/" + str(args['attack']) + "/" + "untargeted"):
            os.makedirs(str(args['save']) + "/" + str(args['dataset']) + "/" + str(args['attack']) + "/" + "untargeted")

    for j in range(len(inputs)):
    #    pred = []
        if inception:
    #        pred.append(np.reshape(model.model.predict(adv[j:j + 1]), (data.test_labels[0:1].shape)))
            pred_r = np.reshape(model.model.predict(adv[j:j + 1]), (data.test_labels[0:1].shape))
        else:
     #       pred.append(model.model.predict(adv[j:j + 1]))
            pred_r = model.model.predict(adv[j:j + 1])

        if (np.argmax(pred_r, 1) != np.argmax(targets[j:j + 1], 1)):
            r_average.append(1)
            d_average_l2.append(np.sum((adv[j] - inputs[j]) ** 2) ** .5)
            d_average_l1.append(np.sum(np.abs(adv[j] - inputs[j])))
            d_average_linf.append(np.amax(np.abs(adv[j] - inputs[j])))
        else:
            r_average.append(0)

        if args['show']:
            for i in range(j, j + args['batch_size']):
                target_id = np.argmax(targets[i:i+ 1], 1)
                label_id = np.argmax(labels[i:i+1], 1)
                prev_id = np.argmax(np.reshape(model.model.predict(inputs[i:i + 1]),
                                                (data.test_labels[0:1].shape)), 1)
                adv_id = np.argmax(np.reshape(model.model.predict(adv[i:i + 1]), (data.test_labels[0:1].shape)), 1)
                suffix = "id{}_seq{}_lbl{}_prev{}_adv{}_{}_l1_{:.3f}_l2_{:.3f}_linf_{:.3f}".format(
                    true_ids[i],
                    target_id,
                    label_id,
                    prev_id,
                    adv_id,
                    adv_id != target_id,
                    np.sum(np.abs(adv[i] - inputs[i])),
                    np.sum((adv[i] - inputs[i]) ** 2) ** .5,
                    np.amax(np.abs(adv[i] - inputs[i])))

                show(inputs[i:i + 1], str(args['save']) + "/" + str(args['dataset']) + "/" + str(
                    args['attack']) + "/" + "untargeted" + "/original_{}.png".format(suffix))
                show(adv[i:i + 1], str(args['save']) + "/" + str(args['dataset']) + "/" + str(
                    args['attack']) + "/" + "untargeted" + "/adversarial_{}.png".format(suffix))
                #print("save " + str(i) + " orgin & adver !!!!!!!!!!!!!!!!!!!!!!!!!")

    queryl23 = np.sqrt(queryl2) / inputs.shape[1] / inputs.shape[2] / inputs.shape[3]


    print(np.array(d_average_l2))
    print('average_L2_mean', np.mean(d_average_l2))
    print('average_L1_mean', np.mean(d_average_l1))
    print('average_Li_mean', np.mean(d_average_linf))
    print('average__prob', np.mean(r_average))

    print('smallest_query_count', np.min(querycount))
    print('mean_query_count', np.mean(querycount))
    print('largest_query_count', np.max(querycount))

   # print('smallest_query_l2_first_success', np.min(queryl23))
    #print('mean_query_l2_first_success', np.mean(queryl23))
   # print('largest_query_l2_first_success', np.max(queryl23))


def l0_computation(args, data, model, adv, inception, inputs, targets, labels, true_ids):
    r_best = []
    d_best_l1 = []
    r_average = []
    d_average_l1 = []
    r_worst = []
    d_worst_l1 = []

    if args['show']:
        if not os.path.exists(str(args['save']) + "/" + str(args['dataset']) + "/" + str(args['attack'])):
            os.makedirs(str(args['save']) + "/" + str(args['dataset']) + "/" + str(args['attack']))

    for i in range(0, len(inputs), args['target_number']):
        pred = []
        for j in range(i, i + args['target_number']):
            if inception:
                pred.append(np.reshape(model.model.predict(adv[j:j + 1]), (data.test_labels[0:1].shape)))
            else:
                pred.append(model.model.predict(adv[j:j + 1]))

        dist_l1 = 1e10
        dist_l1_index = 1e10

        for k, j in enumerate(range(i, i + args['target_number'])):
            if np.argmax(pred[k], 1) == np.argmax(targets[j:j + 1], 1):
                #if np.array(np.nonzero(adv[j]-inputs[j])).shape[1] < dist_l1:
                if np.array(np.nonzero(np.where(np.abs(adv[j]-inputs[j]) < 1e-7, 0, adv[j]-inputs[j]))).shape[1] < dist_l1:
                    dist_l1 = np.array(np.nonzero(np.where(np.abs(adv[j]-inputs[j]) < 1e-7, 0, adv[j]-inputs[j]))).shape[1]
                    #abc = np.array(adv[j]-inputs[j])
                    #print(np.nonzero(np.where(adv[j] - inputs[j] < 1e-8, 0, adv[j] - inputs[j])))
                    dist_l1_index = j
        if dist_l1_index != 1e10:
            d_best_l1.append(np.array(np.nonzero(np.where(np.abs(adv[dist_l1_index]-inputs[dist_l1_index]) < 1e-7, 0,
                                                          adv[dist_l1_index]-inputs[dist_l1_index]))).shape[1])
            r_best.append(1)
        else:
            r_best.append(0)

        rand_int = np.random.randint(i, i + args['target_number'])
        if inception:
            pred_r = np.reshape(model.model.predict(adv[rand_int:rand_int + 1]), (data.test_labels[0:1].shape))
        else:
            pred_r = model.model.predict(adv[rand_int:rand_int + 1])
        if np.argmax(pred_r, 1) == np.argmax(targets[rand_int:rand_int + 1], 1):
            r_average.append(1)
            d_average_l1.append(np.array(np.nonzero(np.where(np.abs(adv[rand_int]-inputs[rand_int]) < 1e-7, 0,
                                                             adv[rand_int]-inputs[rand_int]))).shape[1])
        else:
            r_average.append(0)

        dist_l1 = 0
        dist_l1_index = 1e10
        for k, j in enumerate(range(i, i + args['target_number'])):
            if (np.argmax(pred[k], 1) != np.argmax(targets[j:j + 1], 1)):
                r_worst.append(0)
                dist_l1_index = 1e10
                break
            else:
                if np.array(np.nonzero(np.where(np.abs(adv[j]-inputs[j]) < 1e-7, 0, adv[j]-inputs[j]))).shape[1] > dist_l1:
                    dist_l1 = np.array(np.nonzero(np.where(np.abs(adv[j]-inputs[j]) < 1e-7, 0, adv[j]-inputs[j]))).shape[1]
                    dist_l1_index = j

        if dist_l1_index != 1e10:
            d_worst_l1.append(np.array(np.nonzero(np.where(np.abs(adv[dist_l1_index]-inputs[dist_l1_index]) < 1e-7, 0,
                                                           adv[dist_l1_index]-inputs[dist_l1_index]))).shape[1])
            r_worst.append(1)

        if args['show']:
            for j in range(i, i + args['batch_size']):
                target_id = np.argmax(targets[j:j + 1], 1)
                label_id = np.argmax(labels[j:j + 1], 1)
                prev_id = np.argmax(np.reshape(model.model.predict(inputs[j:j + 1]),
                                               (data.test_labels[0:1].shape)), 1)
                adv_id = np.argmax(np.reshape(model.model.predict(adv[j:j + 1]), (data.test_labels[0:1].shape)), 1)
                suffix = "id{}_seq{}_lbl{}_prev{}_adv{}_{}_l1_{:.3f}_l2_{:.3f}_linf_{:.3f}".format(
                    true_ids[i],
                    target_id,
                    label_id,
                    prev_id,
                    adv_id,
                    adv_id == target_id,
                    np.sum(np.abs(adv[j] - inputs[j])),
                    np.sum((adv[j] - inputs[j]) ** 2) ** .5,
                    np.amax(np.abs(adv[j] - inputs[j])))

                show(inputs[j:j + 1], str(args['save']) + "/" + str(args['dataset']) + "/" + str(
                    args['attack']) + "/original_{}.png".format(suffix))
                show(adv[j:j + 1], str(args['save']) + "/" + str(args['dataset']) + "/" + str(
                    args['attack']) + "/adversarial_{}.png".format(suffix))

    print('best_case_L0_mean', np.mean(d_best_l1))
    print('best_case_prob', np.mean(r_best))
    print('average_case_L0_mean', np.mean(d_average_l1))
    print('average_case_prob', np.mean(r_average))
    print('worst_case_L0_mean', np.mean(d_worst_l1))
    print('worst_case_prob', np.mean(r_worst))


def main(args):
 #   gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.7)
    with tf.Session() as sess:
        if args['dataset'] == 'mnist':
            data, model = MNIST(), MNISTModel("models/mnist", sess)
            handpick = False
            inception = False
        if args['dataset'] == "cifar":
            data, model = CIFAR(), CIFARModel("models/cifar", sess)
            handpick = True
            inception = False
        if args['dataset'] == "imagenet":
            data, model = ImageNet(args['seed_imagenet']), InceptionModel(sess)
            handpick = True
            inception = True

        if args['adversarial'] != "none":
            model = MNISTModel("models/mnist_cwl2_admm" + str(args['adversarial']), sess)

        if args['temp'] and args['dataset'] == 'mnist':
            model = MNISTModel("models/mnist-distilled-" + str(args['temp']), sess)
        if args['temp'] and args['dataset'] == 'cifar':
            model = CIFARModel("models/cifar-distilled-" + str(args['temp']), sess)

        inputs, targets, labels, true_ids = generate_data(data, model, samples=args['numimg'], targeted=args['targeted'],
                                        start=0, inception=inception, handpick=handpick, seed=args['seed'])
        #data, model, samples, targeted=True, target_num=9, start=0, inception=False, seed=3, handpick=False

        #print(true_ids)
        if args['attack'] == 'L2C':
            attack = CarliniL2(sess, model, batch_size=args['batch_size'], max_iterations=args['maxiter'],
                               confidence=args['conf'], targeted=args['targeted'],
                               binary_search_steps=args['binary_steps'],
                               abort_early=args['abort_early'])


        if args['attack'] == 'L2BB':
            # score-based ZO-ADMM attack
            attack = LADMMBB(sess, model, batch_size=args['batch_size'], max_iterations=args['maxiter'],
                             targeted=args['targeted'], confidence=args['conf'],
                             binary_search_steps=args['iteration_steps'], ro=args['ro'],
                             abort_early=args['abort_early'], gama=args['gama'], epi=args['epi'], alpha=args['alpha'])


        timestart = time.time()
    #    adv = attack.attack(inputs, targets)
        adv, querycount, queryl2 = attack.attack(inputs, targets)
        timeend = time.time()
        print("Took", timeend - timestart, "seconds to run", len(inputs), "samples.\n")
        
        #print("step1!!!!!!!!!!!!!") 
        if args['train']:
            np.save('labels_train.npy', labels)
            np.save(str(args['attack']) + '_train.npy', adv)
        #print("step2!!!!!!!!!!!!!!!!!")
        if (args['conf'] != 0):
            model = MNISTModel("models/mnist-distilled-100", sess)

        if args['targeted']:
            l1_l2_li_computation(args, data, model, adv, inception, inputs,
                                targets, labels, true_ids, querycount, queryl2)
        else:
            #print("yes!!!!!!!!!!!!!!!!!!!!")
            l2_computation(args, data, model, adv, inception, inputs, targets, labels, true_ids, querycount, queryl2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--dataset", choices=["mnist", "cifar", "imagenet"], default="mnist",
                        help="dataset to use") #mnist dataset
    parser.add_argument("-n", "--numimg", type=int, default=1, help="number of images to attack") #试过500，但是只保存了1张且false了
    parser.add_argument("-b", "--batch_size", type=int, default=1, help="batch size") #batch size的作用？
    parser.add_argument("-m", "--maxiter", type=int, default=1000, help="max iterations per bss") #bss？
    #parser.add_argument("-m1", "--maxiter_1", type=int, default=1000, help="max iterations per bss")
    parser.add_argument("-is", "--iteration_steps", type=int, default=100, help="number of iteration")
    parser.add_argument("-ro", "--ro", type=float, default=10, help="value of ro")
    parser.add_argument("-bs", "--binary_steps", type=int, default=8, help="number of bss")
    parser.add_argument("-ae", "--abort_early", action='store_true', default=False,
                        help="abort binary search step early when losses stop decreasing")
    parser.add_argument("-cf", "--conf", type=int, default=0, help='Set attack confidence for transferability tests')
    parser.add_argument("-imgsd", "--seed_imagenet", type=int, default=1,
                        help='random seed for pulling images from ImageNet test set')
    parser.add_argument("-sd", "--seed", type=int, default=373,
                        help='random seed for pulling images from data set')
    parser.add_argument("-sh", "--show", action='store_true', default=True,
                        help='save original and adversarial images to save directory') #要做到每一个sample都被保存下来
    parser.add_argument("-ta", "--targeted", action='store_true', default=False,
                        help='targeted or untargeted attack')
    parser.add_argument("-s", "--save", default="./saves", help="save directory")
    parser.add_argument("-a", "--attack",
                        default="L2BB",
                        help="attack algorithm")
    parser.add_argument("-tn", "--target_number", type=int, default=1, help="number of targets for one input")
    parser.add_argument("-tr", "--train", action='store_true', default=False,
                        help="save adversarial images generated from train set") # ？？？什么train set
    parser.add_argument("-al", "--alpha", type=float, default=10, help='alpha hyperparameter')
    parser.add_argument("-tp", "--temp", type=int, default=0,
                        help="attack defensively distilled network trained with this temperature") #其实没有train distilled network
    parser.add_argument("-adv", "--adversarial", choices=["none", "l2", "l1", "en", "l2l1", "l2en"], default="none",
                        help="attack network adversarially trained under these examples") 
    parser.add_argument("-be", "--beta", type=float, default=1e-2, help='beta hyperparameter')
    parser.add_argument("-ga", "--gama", type=float, default=1, help='gama hyperparameter')
    parser.add_argument("-ep", "--epi", type=float, default=0.4, help='epison hyperparameter')
    args = vars(parser.parse_args())
    print(args)
    main(args)
