// src/png.ts
//
import { FlateStream } from "../pdf_js/flate_stream";

export interface AnimationFrame {
  width: number;
  height: number;
  xOffset: number;
  yOffset: number;
  delay: number;
  disposeOp: number;
  blendOp: number;
  data: number[];
  imageData?: ImageData;
  image?: HTMLImageElement;
}

export interface PNGOptions {
  url: string;
  canvas?: HTMLCanvasElement;
  callback?: (png: PNG) => void;
}

const APNG_DISPOSE_OP_BACKGROUND = 1;
const APNG_DISPOSE_OP_PREVIOUS = 2;
const APNG_BLEND_OP_SOURCE = 0;

class PNG {
  private data: Uint8Array;
  private pos: number;
  private palette: number[];
  private imgData: number[];
  private transparency: { [key: string]: number[] };
  private animation: { numFrames: number; numPlays: number; frames: AnimationFrame[] } | null;
  private text: { [key: string]: string };
  width: number;
  height: number;
  private bits: number;
  private colorType: number;
  private compressionMethod: number;
  private filterMethod: number;
  private interlaceMethod: number;
  private colors: number;
  private hasAlphaChannel: boolean;
  private pixelBitlength: number;
  private colorSpace: 'DeviceGray' | 'DeviceRGB';
  private _decodedPalette: Uint8Array | null;

  constructor(data: Uint8Array) {
    this.data = data;
    this.pos = 8; // Skip the default header
    this.palette = [];
    this.imgData = [];
    this.transparency = {};
    this.animation = null;
    this.text = {};
    this._decodedPalette = null;

    this.parse();
  }

  static load({ url, canvas, callback }: PNGOptions) {
    if (typeof canvas === 'function') {
      callback = canvas;
      canvas = undefined;
    }

    const xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'arraybuffer';
    xhr.onload = () => {
      const data = new Uint8Array(xhr.response || xhr.mozResponseArrayBuffer);
      const png = new PNG(data);
      if (canvas) {
        const context = canvas.getContext('2d');
        if (context) {
          png.render(canvas);
        }
      }
      if (callback) {
        callback(png);
      }
    };
    xhr.send(null);
  }

  private parse() {
    let i: number;
    let frame: AnimationFrame | null = null;

    while (true) {
      const chunkSize = this.readUInt32();
      let section = '';
      for (i = 0; i < 4; i++) {
        section += String.fromCharCode(this.data[this.pos++]);
      }

      switch (section) {
        case 'IHDR':
          this.width = this.readUInt32();
          this.height = this.readUInt32();
          this.bits = this.data[this.pos++];
          this.colorType = this.data[this.pos++];
          this.compressionMethod = this.data[this.pos++];
          this.filterMethod = this.data[this.pos++];
          this.interlaceMethod = this.data[this.pos++];
          break;

        case 'acTL':
          this.animation = {
            numFrames: this.readUInt32(),
            numPlays: this.readUInt32() || Infinity,
            frames: []
          };
          break;

        case 'PLTE':
          this.palette = this.read(chunkSize);
          break;

        case 'fcTL':
          if (frame) {
            this.animation!.frames.push(frame);
          }

          this.pos += 4; // skip sequence number
          frame = {
            width: this.readUInt32(),
            height: this.readUInt32(),
            xOffset: this.readUInt32(),
            yOffset: this.readUInt32(),
            delay: (1000 * this.readUInt16()) / (this.readUInt16() || 100),
            disposeOp: this.data[this.pos++],
            blendOp: this.data[this.pos++],
            data: []
          };
          break;

        case 'IDAT':
        case 'fdAT':
          if (section === 'fdAT') {
            this.pos += 4; // skip sequence number
          }

          const data = (frame && frame.data) || this.imgData;
          for (i = 0; i < chunkSize; i++) {
            data.push(this.data[this.pos++]);
          }
          break;

        case 'tRNS':
          this.transparency = {};
          switch (this.colorType) {
            case 3:
              this.transparency.indexed = this.read(chunkSize);
              const short = 255 - this.transparency.indexed.length;
              if (short > 0) {
                for (i = 0; i < short; i++) {
                  this.transparency.indexed.push(255);
                }
              }
              break;
            case 0:
              this.transparency.grayscale = this.read(chunkSize)[0];
              break;
            case 2:
              this.transparency.rgb = this.read(chunkSize);
              break;
          }
          break;

        case 'tEXt':
          const text = this.read(chunkSize);
          const index = text.indexOf(0);
          const key = String.fromCharCode.apply(String, text.slice(0, index));
          this.text[key] = String.fromCharCode.apply(String, text.slice(index + 1));
          break;

        case 'IEND':
          if (frame) {
            this.animation!.frames.push(frame);
          }

          this.colors = [0, 3, 4].includes(this.colorType) ? 1 : 3;
          this.hasAlphaChannel = [4, 6].includes(this.colorType);
          const colors = this.colors + (this.hasAlphaChannel ? 1 : 0);
          this.pixelBitlength = this.bits * colors;
          this.colorSpace = this.colors === 1 ? 'DeviceGray' : 'DeviceRGB';
          this.imgData = new Uint8Array(this.imgData);
          return;

        default:
          this.pos += chunkSize; // Skip unknown section
      }

      this.pos += 4; // Skip CRC

      if (this.pos > this.data.length) {
        throw new Error('Incomplete or corrupt PNG file');
      }
    }
  }

  private read(bytes: number): number[] {
    const result = new Array(bytes);
    for (let i = 0; i < bytes; i++) {
      result[i] = this.data[this.pos++];
    }
    return result;
  }

  private readUInt32(): number {
    const b1 = this.data[this.pos++] << 24;
    const b2 = this.data[this.pos++] << 16;
    const b3 = this.data[this.pos++] << 8;
    const b4 = this.data[this.pos++];
    return b1 | b2 | b3 | b4;
  }

  private readUInt16(): number {
    const b1 = this.data[this.pos++] << 8;
    const b2 = this.data[this.pos++];
    return b1 | b2;
  }

  decodePixels(data: Uint8Array | null = null): Uint8Array {
    if (data === null) {
      data = this.imgData;
    }
    if (data.length === 0) {
      return new Uint8Array(0);
    }

    data = new FlateStream(data, data?.length).getBytes();

    const { width, height } = this;
    const pixelBytes = this.pixelBitlength / 8;

    const pixels = new Uint8Array(width * height * pixelBytes);
    const { length } = data;
    let pos = 0;

    const pass = (x0: number, y0: number, dx: number, dy: number, singlePass = false) => {
      const w = Math.ceil((width - x0) / dx);
      const h = Math.ceil((height - y0) / dy);
      const scanlineLength = pixelBytes * w;
      const buffer = singlePass ? pixels : new Uint8Array(scanlineLength * h);
      let row = 0;
      let c = 0;
      while (row < h && pos < length) {
        var byte, col, i, left, upper;
        switch (data[pos++]) {
          case 0: // None
            for (i = 0; i < scanlineLength; i++) {
              buffer[c++] = data[pos++];
            }
            break;

          case 1: // Sub
            for (i = 0; i < scanlineLength; i++) {
              byte = data[pos++];
              left = i < pixelBytes ? 0 : buffer[c - pixelBytes];
              buffer[c++] = (byte + left) % 256;
            }
            break;

          case 2: // Up
            for (i = 0; i < scanlineLength; i++) {
              byte = data[pos++];
              col = (i - (i % pixelBytes)) / pixelBytes;
              upper =
                row &&
                buffer[
                (row - 1) * scanlineLength +
                col * pixelBytes +
                (i % pixelBytes)
                ];
              buffer[c++] = (upper + byte) % 256;
            }
            break;

          case 3: // Average
            for (i = 0; i < scanlineLength; i++) {
              byte = data[pos++];
              col = (i - (i % pixelBytes)) / pixelBytes;
              left = i < pixelBytes ? 0 : buffer[c - pixelBytes];
              upper =
                row &&
                buffer[
                (row - 1) * scanlineLength +
                col * pixelBytes +
                (i % pixelBytes)
                ];
              buffer[c++] = (byte + Math.floor((left + upper) / 2)) % 256;
            }
            break;

          case 4: // Paeth
            for (i = 0; i < scanlineLength; i++) {
              var paeth, upperLeft;
              byte = data[pos++];
              col = (i - (i % pixelBytes)) / pixelBytes;
              left = i < pixelBytes ? 0 : buffer[c - pixelBytes];

              if (row === 0) {
                upper = upperLeft = 0;
              } else {
                upper =
                  buffer[
                  (row - 1) * scanlineLength +
                  col * pixelBytes +
                  (i % pixelBytes)
                  ];
                upperLeft =
                  col &&
                  buffer[
                  (row - 1) * scanlineLength +
                  (col - 1) * pixelBytes +
                  (i % pixelBytes)
                  ];
              }

              const p = left + upper - upperLeft;
              const pa = Math.abs(p - left);
              const pb = Math.abs(p - upper);
              const pc = Math.abs(p - upperLeft);

              if (pa <= pb && pa <= pc) {
                paeth = left;
              } else if (pb <= pc) {
                paeth = upper;
              } else {
                paeth = upperLeft;
              }

              buffer[c++] = (byte + paeth) % 256;
            }
            break;

          default:
            throw new Error(`Invalid filter algorithm: ${data[pos - 1]}`);
        }

        if (!singlePass) {
          let pixelsPos = ((y0 + row * dy) * width + x0) * pixelBytes;
          let bufferPos = row * scanlineLength;
          for (i = 0; i < w; i++) {
            for (let j = 0; j < pixelBytes; j++)
              pixels[pixelsPos++] = buffer[bufferPos++];
            pixelsPos += (dx - 1) * pixelBytes;
          }
        }

        row++;
      }

      return buffer;
    };

    // const paethPredictor = (left: number, above: number, upperLeft: number) => {
    //   const p = left + above - upperLeft;
    //   const pa = Math.abs(p - left);
    //   const pb = Math.abs(p - above);
    //   const pc = Math.abs(p - upperLeft);
    //   return pa <= pb && pa <= pc ? left : pb <= pc ? above : upperLeft;
    // };

    let row = 0;
    const singlePass = this.interlaceMethod === 0;
    pixels.set(pass(0, 0, 1, 1, singlePass));

    if (!singlePass) {
      row += 1;
      const widths = [8, 8, 4, 2, 1];
      for (let pass = 1; pass < 7; pass++) {
        const x = (pass === 4 ? 4 : pass % 4) * widths[pass % 5];
        const y = (pass === 4 ? 4 : Math.floor(pass / 4)) * widths[pass % 5];
        const dx = widths[pass % 5];
        const dy = widths[pass % 5];
        if (row + dy <= height) {
          pixels.set(pass(x, y, dx, dy), row * width * pixelBytes);
        }
      }
    }

    return pixels;
  }

  render(canvas: HTMLCanvasElement) {
    const context = canvas.getContext('2d');
    if (!context) {
      return;
    }

    const { width, height } = this;
    const imageData = context.createImageData(width, height);
    const pixels = this.decodePixels();
    let i = 0;

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const offset = (y * width + x) * 4;
        imageData.data[offset] = pixels[i++];
        imageData.data[offset + 1] = pixels[i++];
        imageData.data[offset + 2] = pixels[i++];
        imageData.data[offset + 3] = pixels[i++];
      }
    }

    context.putImageData(imageData, 0, 0);
  }
}

export default PNG;

