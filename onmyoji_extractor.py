import os, struct, zlib, tempfile, argparse
from tqdm import tqdm
import extractor as ext
from extractor import readuint32, get_ext, get_parser

def decrypt(data):
    data = bytearray(data)
    key = 150
    for i in range(min(len(data), 128)):
        data[i] = data[i] ^ key
        key = (key + 1) % 256
    return data

def unpack(path):
    folder_path = path.replace('.npk', '')
    os.mkdir(folder_path)

    with open(path, 'rb') as f:
        data = f.read(4)

        files = readuint32(f)
        var1 = readuint32(f)
        var2 = readuint32(f)
        var3 = readuint32(f)
        index_offset = readuint32(f)
        f.seek(index_offset)
        index_table = []
        with tempfile.TemporaryFile() as tmp:
            data = f.read(files * 32)

            tmp.write(data)
            tmp.seek(0)
            for _ in range(files):
                file_sign = readuint32(tmp)
                file_unknown = readuint32(tmp)
                file_offset = readuint32(tmp)
                file_length = readuint32(tmp)
                file_original_length = readuint32(tmp)
                file_hash_1 = readuint32(tmp)
                file_hash_2 = readuint32(tmp)
                file_flag = readuint32(tmp)
                index_table.append((
                    file_offset, 
                    file_length,
                    file_original_length, 
                    file_flag,
                    ))

        for i, item in enumerate(index_table):
            file_name = '{:8}.dat'.format(i)
            file_offset, file_length, file_original_length, file_flag = item
            if file_length < 5000:
                continue
            f.seek(file_offset)
            data = f.read(file_length)
            if file_flag & 0x10000:
                data = decrypt(data)

            if file_flag & 1 == 1:
                data = zlib.decompress(data)
                
            ext = get_ext(data)
            file_name = '{:08}.{}'.format(i, ext)
            if ext in ['mesh', 'ktx', 'bnk', 'riff', 'pvr', 'pkm', 'dds']:
                print('{}/{}'.format(i + 1, files))
                file_path = folder_path + '/' + file_name
                with open(file_path, 'wb') as dat:
                    dat.write(data)
                if ext in ['ktx', 'pvr']:
                    os.system('bin\\PVRTexToolCLI.exe -i {} -d -f r8g8b8a8'.format(file_path))
        os.system('del {}\\*.ktx'.format(folder_path))
        os.system('del {}\\*.pvr'.format(folder_path))

def main():
    opt = get_parser()
    unpack(opt.path)


if __name__ == '__main__':
    main()