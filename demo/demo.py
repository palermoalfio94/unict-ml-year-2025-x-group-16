import torch
from torch import nn
from torchvision import transforms
from PIL import Image
import gradio as gr
import numpy as np
# ================================
# Device
# ================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ================================
# Modello Custom CNN (Regressione)
# ================================
class CustomCNN(nn.Module):
    def __init__(self, input_size=(3, 500, 500)):
        super(CustomCNN, self).__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        with torch.no_grad():
            dummy = torch.zeros(1, *input_size)
            dummy = self.features(dummy)
            self.flatten_dim = dummy.numel()

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(self.flatten_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


# ================================
# Caricamento checkpoint
# ================================
checkpoint_path = "fineTune_checkpoint_epoch_29.pt"

checkpoint = torch.load(checkpoint_path, map_location=device)

model = CustomCNN().to(device)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

print(f"Checkpoint caricato (epoch {checkpoint['epoch']})")

# ================================
# Normalizzazione (da training)
# ================================
mean = [0.5721, 0.4503, 0.3027]
std  = [0.2717, 0.2386, 0.2102]

inference_transform = transforms.Compose([
    transforms.Resize((500, 500)),
    transforms.ToTensor(),
    transforms.Normalize(mean=mean, std=std)
])

# ================================
# Funzione di previsione
# ================================

def predict(image):
    # Gradio -> numpy array -> PIL
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)

    image = inference_transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image)

    return float(output.item())


# ================================
# Interfaccia Gradio
# ================================
iface = gr.Interface(
    fn=predict,
    inputs="image",
    outputs="number",
    title="Regressione su immagine",
    description="Carica un'immagine e il modello restituisce la previsione"
)

iface.launch()
