# Ryujinx Streamer

This is an enhanced fork of the popular Nintendo Switch emulator, [Ryujinx](https://github.com/Ryujinx/Ryujinx). We extend the original project for autonomous AI based gameplay.

## Features

1. Stream video footage in real-time
2. Control keyboard and mouse actions programmatically. 

## How it works

### Prerequisites for Ryujinx

- .NET 6.0 SDK
- A Nintendo Switch game in either XCI or NSP format

## Getting Started

### Installation

1. Install the .NET SDK for your OS from here: https://dotnet.microsoft.com/en-us/download
2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Ryujinx-Streamer.git
   ```
3. Build Ryujinx:
   ```bash
   cd Ryujinx
   dotnet build
   ```

### Usage

1. Run the emulator:
   ```bash
   cd Ryujinx
   ./build/Ryujinx
   ```
2. Open your client and connect to `http://localhost:port` where `port` is the port number specified in your configuration.

## Configuration

Modify the `config.json` file to adjust settings like port number, resolution, and control mappings.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the original Ryujinx team for their incredible work on the emulator.
