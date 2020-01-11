import os, struct, zlib, tempfile, argparse
from tqdm import tqdm


def readuint32(f):
    return struct.unpack('I', f.read(4))[0]

def readuint8(f):
    return struct.unpack('B', f.read(1))[0]

def get_ext(data):
    if len(data) == 0:
        return 'none'
    if data[:12] == b'CocosStudio-UI':
        return 'coc'
    elif data[:1] == b'<':
        return 'xml'
    elif data[:1] == b'{':
        return 'json'
    elif data[:3] == b'hit':
        return 'hit'
    elif data[:3] == b'PKM':
        return 'pkm'
    elif data[:3] == b'PVR':
        return 'pvr'
    elif data[:3] == b'DDS':
        return 'dds'
    elif data[1:4] == b'KTX':
        return 'ktx'
    elif data[1:4] == b'PNG':
        return 'png'
    elif data[:4] == bytes([0x34, 0x80, 0xC8, 0xBB]):
        return 'nxm'
    elif data[:4] == bytes([0x14, 0x00, 0x00, 0x00]):
        return 'type1'
    elif data[:4] == bytes([0x04, 0x00, 0x00, 0x00]):
        return 'type2'
    elif data[:4] == bytes([0x00, 0x01, 0x00, 0x00]):
        return 'type3'
    elif data[:4] == b'VANT':
        return 'vant'
    elif data[:4] == b'MDMP':
        return 'mdmp'
    elif data[:4] == b'RGIS':
        return 'rgis'
    elif data[:4] == b'NTRK':
        return 'ntrk'
    elif data[:4] == b'RIFF':
        return 'riff'
    elif data[:4] == b'BKHD':
        return 'bnk'
    elif len(data) < 1000000:
        if b'void' in data or b'main(' in data or b'include' in data or b'float' in data:
            return 'shader'
        if b'technique' in data or b'ifndef' in data:
            return 'shader'
        if b'?xml' in data:
            return 'xml'
        if b'import' in data:
            return 'py'
        if b'1000' in data or b'ssh' in data or b'png' in data or b'tga' in data or b'exit' in data:
            return 'txt'
    return 'dat'

def decrypt(data, keys):
    data = bytearray(data)
    for i in range(len(data)):
        data[i] = data[i] ^ keys[i]
    return data

def unpack(opt):
    keys = []
    folder_path = opt.path.replace('.npk', '')
    os.mkdir(folder_path)
    with open('key.txt') as f:
        for value in f:
            keys.append(int(value))
    max_length = len(keys)


    with open(opt.path, 'rb') as f:
        data = f.read(4)
        pkg_type = None
        if data == b'NXPK':
            pkg_type = 0
        elif data == b'EXPK':
            pkg_type = 1
        else:
            raise Exception('NOT NXPK/EXPK FILE')
        files = readuint32(f)
        # print(files)
        var1 = readuint32(f)
        var2 = readuint32(f)
        var3 = readuint32(f)
        mode = 1 if var1 and var3 else 0
        info_size = 0x28 if mode else 0x1c
        index_offset = readuint32(f)
        f.seek(index_offset)
        index_table = []
        with tempfile.TemporaryFile() as tmp:
            for i in range(files * 28):
                data = readuint8(f)
                if pkg_type:
                    data = data ^ keys[i]
                tmp.write(struct.pack('B', data))
            tmp.seek(0)
            for _ in range(files):
                file_sign = readuint32(tmp)
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
            if file_length >= max_length or file_length < 5000:
                continue
            f.seek(file_offset)
            data = f.read(file_length)
            if pkg_type:
                data = decrypt(data, keys)

            if file_flag == 1:
                data = zlib.decompress(data)
            ext = get_ext(data)
            file_name = '{:08}.{}'.format(i, ext)
            if ext in ['nxm', 'ktx', 'bnk', 'riff', 'pvr', 'pkm', 'dds']:
                print('{}/{}'.format(i + 1, files))
                file_path = folder_path + '/' + file_name
                with open(file_path, 'wb') as dat:
                    dat.write(data)
                if ext in ['ktx', 'pvr']:
                    os.system('bin\\PVRTexToolCLI.exe -i {} -d -f r8g8b8a8'.format(file_path))
        os.system('del {}\\*.ktx'.format(folder_path))
        os.system('del {}\\*.pvr'.format(folder_path))

def get_parser():
    parser = argparse.ArgumentParser(description='EXPK Extractor')
    parser.add_argument('path', type=str)
    opt = parser.parse_args()
    return opt

def main():
    opt = get_parser()
    unpack(opt)


if __name__ == '__main__':
    main()