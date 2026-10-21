# Artemis Background Remover

Artemis Background Remover is a powerful, standalone GUI application designed for removing backgrounds and precisely editing transparency masks of images and avatars.

## Repository Setup (Fork & Clone)

Before setting up the application, fork the original repository to your own GitHub account.

1. Fork the Repository

Open the original repository on GitHub:

https://github.com/df-yamashitamasashi/artemis-bg-remover

Click the Fork button in the top-right corner to create a copy under your own GitHub account.

2. Clone Your Fork

Clone your forked repository to your local machine.

Replace <your-username> with your GitHub username.

git clone https://github.com/<your-username>/artemis-bg-remover.git
cd artemis-bg-remover

3. Add the Original Repository as Upstream

Register the original repository as upstream.

git remote add upstream https://github.com/df-yamashitamasashi/artemis-bg-remover.git

4. Verify Remote Repositories

Run the following command:

git remote -v

Expected output:

origin    https://github.com/<your-username>/artemis-bg-remover.git (fetch)
origin    https://github.com/<your-username>/artemis-bg-remover.git (push)
upstream  https://github.com/df-yamashitamasashi/artemis-bg-remover.git (fetch)
upstream  https://github.com/df-yamashitamasashi/artemis-bg-remover.git (push)

origin: Your forked repository. Push your changes here.

upstream: The original repository. Use it to fetch updates.

Note: For this training exercise, create and merge Pull Requests within your own fork. Do not submit Pull Requests to the original repository.

## Features
- **AI Background Removal**: Automatically remove image backgrounds using `rembg`.
- **Smart Flood Fill**: Intelligently remove contiguous regions of similar colors with an adjustable tolerance slider.
- **Manual Brush Tools**: Use the erase and restore brushes with adjustable brush sizes to fine-tune masks.
- **High-Performance Infinite Zoom & Pan**: A hardware-accelerated viewport-based rendering engine allows zooming up to 4000% without lag.
- **Dark Mode UI**: A premium, modern dark mode interface built with CustomTkinter.

## Installation

We recommend using a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run the main application:

```bash
python main.py
```

### Controls
- **Scroll Wheel**: Vertical Pan / Zoom (with Ctrl/Cmd)
- **Shift + Scroll**: Horizontal Pan
- **Right Click / Middle Click / Space+Drag**: Pan Canvas
- **Left Click**: Apply the selected tool (Fill / Erase / Restore)

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).
See the `LICENSE` file for more details.
