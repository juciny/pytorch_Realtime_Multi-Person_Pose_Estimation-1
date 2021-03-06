import torch
import torch.utils.model_zoo as model_zoo
from training.datasets.coco import get_loader
from network.rtpose_vgg import get_model, use_vgg

# Hyper-params
data_dir = '/data/coco/images'
mask_dir = '/data/coco/'
json_path = '/data/coco/COCO.json'
trunk = 'vgg19'
opt = 'sgd'
momentum = 0.9
weight_decay = 0.000
nesterov = True
inp_size = 368
feat_stride = 8

model_path = './models/'

# Set Training parameters
params = Trainer.TrainParams()
params.exp_name = 'original_rtpose'
params.save_dir = '/extra/tensorboy/models/{}'.format(params.exp_name)
params.ckpt = None  # checkpoint file to load
params.re_init = False

params.max_epoch = 30
params.lr_decay_epoch = {30, 60, 90, 120, 150, 180}
params.init_lr = 2e-4
params.lr_decay = 0.8

params.gpus = [2, 3]
params.batch_size = 20 * len(params.gpus)
params.val_nbatch = 2
params.val_nbatch_epoch = 100
params.save_freq = 3000


print("Loading dataset...")
# load data
train_data = get_loader(json_path, data_dir,
                        mask_dir, inp_size, feat_stride,
                        'vgg', params.batch_size,
                        shuffle=True, training=True)
print('train dataset len: {}'.format(len(train_data.dataset)))

# validation data
valid_data = None
if params.val_nbatch > 0:
    valid_data = get_loader(json_path, data_dir, mask_dir, inp_size,
                            feat_stride, preprocess='vgg', training=False,
                            batch_size=params.batch_size, shuffle=True)
    print('val dataset len: {}'.format(len(valid_data.dataset)))

# model
model = get_model(trunk=trunk)

# load pretrained
if params.ckpt is None:
    use_vgg(model, model_path, trunk)


# Fix the VGG weights first, and then the weights will be released
for i in range(20):
    for param in model.model0[i].parameters():
        param.requires_grad = False

trainable_vars = [param for param in model.parameters() if param.requires_grad]
params.optimizer = torch.optim.SGD(trainable_vars, lr=params.init_lr,
                                   momentum=momentum,
                                   weight_decay=weight_decay,
                                   nesterov=nesterov)
