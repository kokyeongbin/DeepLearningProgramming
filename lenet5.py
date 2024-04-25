# -*- coding: utf-8 -*-
"""LeNET5_초기.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1MLHS5GVntQ2fyTDjrQXS9Yz21w7Pyh07
"""

import numpy as np
from datetime import datetime
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# parameters
RANDOM_SEED = 42
LEARNING_RATE = 0.001
BATCH_SIZE = 32
N_EPOCHS = 15

IMG_SIZE = 32
N_CLASSES = 10

def get_accuracy(model, data_loader, device):
    '''
    전체 data_loader에 대한 예측의 정확도를 계산하는 함수
    '''

    correct_pred = 0
    n = 0

    with torch.no_grad():
        model.eval()
        for X, y_true in data_loader:

            X = X.to(device)
            y_true = y_true.to(device)

            _, y_prob = model(X)
            _, predicted_labels = torch.max(y_prob, 1)

            n += y_true.size(0)
            correct_pred += (predicted_labels == y_true).sum()

    return correct_pred.float() / n

def plot_losses(train_losses, valid_losses):
    '''
    training과 validation loss를 시각화하는 함수
    '''

    # plot style을 seaborn으로 설정
    plt.style.use('seaborn')

    train_losses = np.array(train_losses)
    valid_losses = np.array(valid_losses)

    fig, ax = plt.subplots(figsize = (8, 4.5))

    ax.plot(train_losses, color='red', label='Training loss')
    ax.plot(valid_losses, color='blue', label='Validation loss')
    ax.set(title="Loss over epochs",
            xlabel='Epoch',
            ylabel='Loss')
    ax.legend()
    fig.show()

    # plot style을 기본값으로 설정
    plt.style.use('default')

def train(train_loader, model, criterion, optimizer, device):
    '''
    training loop의 training 단계에 대한 함수
    '''

    model.train()
    running_loss = 0

    for X, y_true in train_loader:

        optimizer.zero_grad()

        X = X.to(device)
        y_true = y_true.to(device)

        # 순전파
        y_hat, _ = model(X)
        loss = criterion(y_hat, y_true)
        running_loss += loss.item() * X.size(0)

        # 역전파
        loss.backward()
        optimizer.step()

    epoch_loss = running_loss / len(train_loader.dataset)
    return model, optimizer, epoch_loss

def validate(valid_loader, model, criterion, device):
    '''
    training loop의 validation 단계에 대한 함수
    '''

    model.eval()
    running_loss = 0

    for X, y_true in valid_loader:

        X = X.to(device)
        y_true = y_true.to(device)

        # 순전파와 손실 기록하기
        y_hat, _ = model(X)
        loss = criterion(y_hat, y_true)
        running_loss += loss.item() * X.size(0)

    epoch_loss = running_loss / len(valid_loader.dataset)

    return model, epoch_loss

def training_loop(model, criterion, optimizer, train_loader, valid_loader, epochs, device, print_every=1):
    '''
    전체 training loop를 정의하는 함수
    '''

    # metrics를 저장하기 위한 객체 설정
    best_loss = 1e10
    train_losses = []
    valid_losses = []

    # model 학습하기
    for epoch in range(0, epochs):
         # Training 시작 전 시간 기록
        start_time = datetime.now()

        # training
        model, optimizer, train_loss = train(train_loader, model, criterion, optimizer, device)
        train_losses.append(train_loss)

        # validation
        with torch.no_grad():
            model, valid_loss = validate(valid_loader, model, criterion, device)
            valid_losses.append(valid_loss)

        if epoch % print_every == (print_every - 1):

            # Training 종료 시간 기록
            end_time = datetime.now()
            duration = end_time - start_time

            train_acc = get_accuracy(model, train_loader, device=device)
            valid_acc = get_accuracy(model, valid_loader, device=device)

            print(f'{datetime.now().time().replace(microsecond=0)} --- '
                  f'Epoch: {epoch}\t'
                  f'Train loss: {train_loss:.4f}\t'
                  f'Valid loss: {valid_loss:.4f}\t'
                  f'Train accuracy: {100 * train_acc:.2f}\t'
                  f'Valid accuracy: {100 * valid_acc:.2f}\t'
                  f'Duration: {duration}')

    plot_losses(train_losses, valid_losses)

    return model, optimizer, (train_losses, valid_losses)

# transforms 정의하기
transforms = transforms.Compose([transforms.Resize((32, 32)),
                                 transforms.ToTensor()])

# data set 다운받고 생성하기
train_dataset = datasets.MNIST(root='mnist_data',
                               train=True,
                               transform=transforms,
                               download=True)

valid_dataset = datasets.MNIST(root='mnist_data',
                               train=False,
                               transform=transforms)

# data loader 정의하기
train_loader = DataLoader(dataset=train_dataset,
                          batch_size=BATCH_SIZE,
                          shuffle=True)

valid_loader = DataLoader(dataset=valid_dataset,
                          batch_size=BATCH_SIZE,
                          shuffle=False)

# 불러온 MNIST data 확인하기
ROW_IMG = 10
N_ROWS = 5

fig = plt.figure()
for index in range(1, ROW_IMG * N_ROWS + 1):
    plt.subplot(N_ROWS, ROW_IMG, index)
    plt.axis('off')
    plt.imshow(train_dataset.data[index], cmap='gray_r')
fig.suptitle('MNIST Dataset - preview');

class LeNet5_Tanh(nn.Module):

    def __init__(self, n_classes):
        super(LeNet5_Tanh, self).__init__()

        self.feature_extractor = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5, stride=1),
            nn.Tanh(),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=6, out_channels=16, kernel_size=5, stride=1),
            nn.Tanh(),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=16, out_channels=120, kernel_size=5, stride=1),
            nn.Tanh()
        )

        self.classifier = nn.Sequential(
            nn.Linear(in_features=120, out_features=84),
            nn.Tanh(),
            nn.Linear(in_features=84, out_features=n_classes),
        )


    def forward(self, x):
        x = self.feature_extractor(x)
        x = torch.flatten(x, 1)
        logits = self.classifier(x)
        probs = F.log_softmax(logits, dim=1)
        return logits, probs

class LeNet5_ReLU(nn.Module):

    def __init__(self, n_classes):
        super(LeNet5_ReLU, self).__init__()

        self.feature_extractor = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5, stride=1),
            nn.ReLU(),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=6, out_channels=16, kernel_size=5, stride=1),
            nn.ReLU(),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=16, out_channels=120, kernel_size=5, stride=1),
            nn.ReLU()
        )

        self.classifier = nn.Sequential(
            nn.Linear(in_features=120, out_features=84),
            nn.Tanh(),
            nn.Linear(in_features=84, out_features=n_classes),
        )


    def forward(self, x):
        x = self.feature_extractor(x)
        x = torch.flatten(x, 1)
        logits = self.classifier(x)
        probs = F.log_softmax(logits, dim=1)
        return logits, probs

class LeNet5_LeakyReLU(nn.Module):

    def __init__(self, n_classes):
        super(LeNet5_LeakyReLU, self).__init__()

        self.feature_extractor = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5, stride=1),
            nn.LeakyReLU(0.1),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=6, out_channels=16, kernel_size=5, stride=1),
            nn.LeakyReLU(0.1),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=16, out_channels=120, kernel_size=5, stride=1),
            nn.LeakyReLU(0.1)
        )

        self.classifier = nn.Sequential(
            nn.Linear(in_features=120, out_features=84),
            nn.Tanh(),
            nn.Linear(in_features=84, out_features=n_classes),
        )


    def forward(self, x):
        x = self.feature_extractor(x)
        x = torch.flatten(x, 1)
        logits = self.classifier(x)
        probs = F.log_softmax(logits, dim=1)
        return logits, probs

class LeNet5_ParametricReLU(nn.Module):

    def __init__(self, n_classes):
        super(LeNet5_ParametricReLU, self).__init__()

        self.feature_extractor = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5, stride=1),
            nn.PReLU(),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=6, out_channels=16, kernel_size=5, stride=1),
            nn.PReLU(),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=16, out_channels=120, kernel_size=5, stride=1),
            nn.PReLU()
        )

        self.classifier = nn.Sequential(
            nn.Linear(in_features=120, out_features=84),
            nn.Tanh(),
            nn.Linear(in_features=84, out_features=n_classes),
        )


    def forward(self, x):
        x = self.feature_extractor(x)
        x = torch.flatten(x, 1)
        logits = self.classifier(x)
        probs = F.log_softmax(logits, dim=1)
        return logits, probs

class LeNet5_ExponentialLinearUnit(nn.Module):

    def __init__(self, n_classes):
        super(LeNet5_ExponentialLinearUnit, self).__init__()

        self.feature_extractor = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5, stride=1),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=6, out_channels=16, kernel_size=5, stride=1),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=2),
            nn.Conv2d(in_channels=16, out_channels=120, kernel_size=5, stride=1),
            nn.ELU(),
        )

        self.classifier = nn.Sequential(
            nn.Linear(in_features=120, out_features=84),
            nn.Tanh(),
            nn.Linear(in_features=84, out_features=n_classes),
        )


    def forward(self, x):
        x = self.feature_extractor(x)
        x = torch.flatten(x, 1)
        logits = self.classifier(x)
        probs = F.log_softmax(logits, dim=1)
        return logits, probs

torch.manual_seed(RANDOM_SEED)

model = LeNet5_Tanh(N_CLASSES).to(DEVICE)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
criterion = nn.CrossEntropyLoss()
model, optimizer, _ = training_loop(model, criterion, optimizer, train_loader,
                                    valid_loader, N_EPOCHS, DEVICE)

# Test dataset에 대한 성능(accuracy) 출력
test_acc = get_accuracy(model, valid_loader, device=DEVICE)
print(f'Test accuracy: {100 * test_acc:.2f}%')

# 정확하게 분류한 10개 sample 랜덤 선택 및 출력
model.eval()
with torch.no_grad():
    correct_samples = []
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        correct_indices = (predicted == labels).nonzero()[:, 0]
        correct_samples.extend(correct_indices.cpu().numpy().tolist())
        if len(correct_samples) >= 10:
            break

# 선택된 정확하게 분류된 샘플 출력
fig, axs = plt.subplots(2, 5, figsize=(15, 6))
for i, index in enumerate(correct_samples):
    if i < 10:  # 10개의 샘플만 출력
        image = valid_dataset[index][0].squeeze().cpu().numpy()
        label = labels[index].item()
        axs[i // 5, i % 5].imshow(image, cmap='gray_r')
        axs[i // 5, i % 5].set_title(f'Label: {label}')
        axs[i // 5, i % 5].axis('off')
plt.show()

# 잘못 분류된 샘플 찾기 및 출력
model.eval()
incorrect_samples = []
incorrect_predictions = []
correct_labels = []
with torch.no_grad():
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        incorrect_indices = (predicted != labels).nonzero()[:, 0]
        incorrect_samples.extend(images[incorrect_indices].cpu().numpy())
        incorrect_predictions.extend(predicted[incorrect_indices].cpu().numpy())
        correct_labels.extend(labels[incorrect_indices].cpu().numpy())

# 모든 잘못 분류된 샘플 출력
fig, axs = plt.subplots((len(incorrect_samples) + 4) // 5, 5, figsize=(15, 3 * ((len(incorrect_samples) + 4) // 5)))
for i in range(len(incorrect_samples)):
    row = i // 5
    col = i % 5
    image = incorrect_samples[i].squeeze()
    predicted_label = incorrect_predictions[i]
    true_label = correct_labels[i]
    axs[row, col].imshow(image, cmap='gray_r')
    axs[row, col].set_title(f'Predicted: {predicted_label}, True: {true_label}')
    axs[row, col].axis('off')
plt.tight_layout()
plt.show()

torch.manual_seed(RANDOM_SEED)

model = LeNet5_ReLU(N_CLASSES).to(DEVICE)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
criterion = nn.CrossEntropyLoss()
model, optimizer, _ = training_loop(model, criterion, optimizer, train_loader,
                                    valid_loader, N_EPOCHS, DEVICE)

# Test dataset에 대한 성능(accuracy) 출력
test_acc = get_accuracy(model, valid_loader, device=DEVICE)
print(f'Test accuracy: {100 * test_acc:.2f}%')

# 정확하게 분류한 10개 sample 랜덤 선택 및 출력
model.eval()
with torch.no_grad():
    correct_samples = []
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        correct_indices = (predicted == labels).nonzero()[:, 0]
        correct_samples.extend(correct_indices.cpu().numpy().tolist())
        if len(correct_samples) >= 10:
            break

# 선택된 정확하게 분류된 샘플 출력
fig, axs = plt.subplots(2, 5, figsize=(15, 6))
for i, index in enumerate(correct_samples):
    if i < 10:  # 10개의 샘플만 출력
        image = valid_dataset[index][0].squeeze().cpu().numpy()
        label = labels[index].item()
        axs[i // 5, i % 5].imshow(image, cmap='gray_r')
        axs[i // 5, i % 5].set_title(f'Label: {label}')
        axs[i // 5, i % 5].axis('off')
plt.show()

# 잘못 분류된 샘플 찾기 및 출력
model.eval()
incorrect_samples = []
incorrect_predictions = []
correct_labels = []
with torch.no_grad():
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        incorrect_indices = (predicted != labels).nonzero()[:, 0]
        incorrect_samples.extend(images[incorrect_indices].cpu().numpy())
        incorrect_predictions.extend(predicted[incorrect_indices].cpu().numpy())
        correct_labels.extend(labels[incorrect_indices].cpu().numpy())

# 모든 잘못 분류된 샘플 출력
fig, axs = plt.subplots((len(incorrect_samples) + 4) // 5, 5, figsize=(15, 3 * ((len(incorrect_samples) + 4) // 5)))
for i in range(len(incorrect_samples)):
    row = i // 5
    col = i % 5
    image = incorrect_samples[i].squeeze()
    predicted_label = incorrect_predictions[i]
    true_label = correct_labels[i]
    axs[row, col].imshow(image, cmap='gray_r')
    axs[row, col].set_title(f'Predicted: {predicted_label}, True: {true_label}')
    axs[row, col].axis('off')
plt.tight_layout()
plt.show()

torch.manual_seed(RANDOM_SEED)

model = LeNet5_LeakyReLU(N_CLASSES).to(DEVICE)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
criterion = nn.CrossEntropyLoss()
model, optimizer, _ = training_loop(model, criterion, optimizer, train_loader,
                                    valid_loader, N_EPOCHS, DEVICE)

# Test dataset에 대한 성능(accuracy) 출력
test_acc = get_accuracy(model, valid_loader, device=DEVICE)
print(f'Test accuracy: {100 * test_acc:.2f}%')

# 정확하게 분류한 10개 sample 랜덤 선택 및 출력
model.eval()
with torch.no_grad():
    correct_samples = []
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        correct_indices = (predicted == labels).nonzero()[:, 0]
        correct_samples.extend(correct_indices.cpu().numpy().tolist())
        if len(correct_samples) >= 10:
            break

# 선택된 정확하게 분류된 샘플 출력
fig, axs = plt.subplots(2, 5, figsize=(15, 6))
for i, index in enumerate(correct_samples):
    if i < 10:  # 10개의 샘플만 출력
        image = valid_dataset[index][0].squeeze().cpu().numpy()
        label = labels[index].item()
        axs[i // 5, i % 5].imshow(image, cmap='gray_r')
        axs[i // 5, i % 5].set_title(f'Label: {label}')
        axs[i // 5, i % 5].axis('off')
plt.show()

# 잘못 분류된 샘플 찾기 및 출력
model.eval()
incorrect_samples = []
incorrect_predictions = []
correct_labels = []
with torch.no_grad():
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        incorrect_indices = (predicted != labels).nonzero()[:, 0]
        incorrect_samples.extend(images[incorrect_indices].cpu().numpy())
        incorrect_predictions.extend(predicted[incorrect_indices].cpu().numpy())
        correct_labels.extend(labels[incorrect_indices].cpu().numpy())

# 모든 잘못 분류된 샘플 출력
fig, axs = plt.subplots((len(incorrect_samples) + 4) // 5, 5, figsize=(15, 3 * ((len(incorrect_samples) + 4) // 5)))
for i in range(len(incorrect_samples)):
    row = i // 5
    col = i % 5
    image = incorrect_samples[i].squeeze()
    predicted_label = incorrect_predictions[i]
    true_label = correct_labels[i]
    axs[row, col].imshow(image, cmap='gray_r')
    axs[row, col].set_title(f'Predicted: {predicted_label}, True: {true_label}')
    axs[row, col].axis('off')
plt.tight_layout()
plt.show()

torch.manual_seed(RANDOM_SEED)

model = LeNet5_ParametricReLU(N_CLASSES).to(DEVICE)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
criterion = nn.CrossEntropyLoss()
model, optimizer, _ = training_loop(model, criterion, optimizer, train_loader,
                                    valid_loader, N_EPOCHS, DEVICE)

# Test dataset에 대한 성능(accuracy) 출력
test_acc = get_accuracy(model, valid_loader, device=DEVICE)
print(f'Test accuracy: {100 * test_acc:.2f}%')

# 정확하게 분류한 10개 sample 랜덤 선택 및 출력
model.eval()
with torch.no_grad():
    correct_samples = []
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        correct_indices = (predicted == labels).nonzero()[:, 0]
        correct_samples.extend(correct_indices.cpu().numpy().tolist())
        if len(correct_samples) >= 10:
            break

# 선택된 정확하게 분류된 샘플 출력
fig, axs = plt.subplots(2, 5, figsize=(15, 6))
for i, index in enumerate(correct_samples):
    if i < 10:  # 10개의 샘플만 출력
        image = valid_dataset[index][0].squeeze().cpu().numpy()
        label = labels[index].item()
        axs[i // 5, i % 5].imshow(image, cmap='gray_r')
        axs[i // 5, i % 5].set_title(f'Label: {label}')
        axs[i // 5, i % 5].axis('off')
plt.show()

# 잘못 분류된 샘플 찾기 및 출력
model.eval()
incorrect_samples = []
incorrect_predictions = []
correct_labels = []
with torch.no_grad():
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        incorrect_indices = (predicted != labels).nonzero()[:, 0]
        incorrect_samples.extend(images[incorrect_indices].cpu().numpy())
        incorrect_predictions.extend(predicted[incorrect_indices].cpu().numpy())
        correct_labels.extend(labels[incorrect_indices].cpu().numpy())

# 모든 잘못 분류된 샘플 출력
fig, axs = plt.subplots((len(incorrect_samples) + 4) // 5, 5, figsize=(15, 3 * ((len(incorrect_samples) + 4) // 5)))
for i in range(len(incorrect_samples)):
    row = i // 5
    col = i % 5
    image = incorrect_samples[i].squeeze()
    predicted_label = incorrect_predictions[i]
    true_label = correct_labels[i]
    axs[row, col].imshow(image, cmap='gray_r')
    axs[row, col].set_title(f'Predicted: {predicted_label}, True: {true_label}')
    axs[row, col].axis('off')
plt.tight_layout()
plt.show()

torch.manual_seed(RANDOM_SEED)

model = LeNet5_ExponentialLinearUnit(N_CLASSES).to(DEVICE)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
criterion = nn.CrossEntropyLoss()
model, optimizer, _ = training_loop(model, criterion, optimizer, train_loader,
                                    valid_loader, N_EPOCHS, DEVICE)

# Test dataset에 대한 성능(accuracy) 출력
test_acc = get_accuracy(model, valid_loader, device=DEVICE)
print(f'Test accuracy: {100 * test_acc:.2f}%')

# 정확하게 분류한 10개 sample 랜덤 선택 및 출력
model.eval()
with torch.no_grad():
    correct_samples = []
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        correct_indices = (predicted == labels).nonzero()[:, 0]
        correct_samples.extend(correct_indices.cpu().numpy().tolist())
        if len(correct_samples) >= 10:
            break

# 선택된 정확하게 분류된 샘플 출력
fig, axs = plt.subplots(2, 5, figsize=(15, 6))
for i, index in enumerate(correct_samples):
    if i < 10:  # 10개의 샘플만 출력
        image = valid_dataset[index][0].squeeze().cpu().numpy()
        label = labels[index].item()
        axs[i // 5, i % 5].imshow(image, cmap='gray_r')
        axs[i // 5, i % 5].set_title(f'Label: {label}')
        axs[i // 5, i % 5].axis('off')
plt.show()

# 잘못 분류된 샘플 찾기 및 출력
model.eval()
incorrect_samples = []
incorrect_predictions = []
correct_labels = []
with torch.no_grad():
    for images, labels in valid_loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        outputs, _ = model(images)
        _, predicted = torch.max(outputs, 1)
        incorrect_indices = (predicted != labels).nonzero()[:, 0]
        incorrect_samples.extend(images[incorrect_indices].cpu().numpy())
        incorrect_predictions.extend(predicted[incorrect_indices].cpu().numpy())
        correct_labels.extend(labels[incorrect_indices].cpu().numpy())

# 모든 잘못 분류된 샘플 출력
fig, axs = plt.subplots((len(incorrect_samples) + 4) // 5, 5, figsize=(15, 3 * ((len(incorrect_samples) + 4) // 5)))
for i in range(len(incorrect_samples)):
    row = i // 5
    col = i % 5
    image = incorrect_samples[i].squeeze()
    predicted_label = incorrect_predictions[i]
    true_label = correct_labels[i]
    axs[row, col].imshow(image, cmap='gray_r')
    axs[row, col].set_title(f'Predicted: {predicted_label}, True: {true_label}')
    axs[row, col].axis('off')
plt.tight_layout()
plt.show()