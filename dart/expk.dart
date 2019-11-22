import 'dart:io';
import 'dart:typed_data';
import 'dart:convert';

bool listEquals<T>(List<T> a, List<T> b) {
  if (a == null)
    return b == null;
  if (b == null || a.length != b.length)
    return false;
  for (int index = 0; index < a.length; index += 1) {
    if (a[index] != b[index])
      return false;
  }
  return true;
}

String getExt(content) {
  if (content.length == 0) {
    return 'none';
  }
  else if (listEquals(content.sublist(0, 4), ascii.encode('RIFF'))){
    return 'riff';
  }
  else if (listEquals(content.sublist(0, 4), ascii.encode('BKHD'))){
    return 'bnk';
  }
  else if (listEquals(content.sublist(1, 4), ascii.encode('KTX'))){
    return 'ktx';
  }
  else if (listEquals(content.sublist(0, 4), [0x34, 0x80, 0xC8, 0xBB])){
    return 'nxm';
  }
  return 'dat';
}

int getUint32(content, position) {
  var b = content.sublist(position, position + 4);
  var c = b.reversed.toList();
  return ByteData.view(Uint8List.fromList(c).buffer).getUint32(0);
}

Map getIndex(content, position){
  var index = new Map();
  index['file_offset'] = getUint32(content, position + 4);
  index['file_length'] = getUint32(content, position + 8);
  index['file_original_length'] = getUint32(content, position + 12);
  index['file_flag'] = getUint32(content, position + 24);
  return index;
}

decrypt(content, keys) {
  for (var i = 0; i < content.length; i++) {
    content[i] = content[i] ^ keys[i];
  }
  return content;
}

void main(List<String> arguments) {
  if (arguments.length != 1){
    stderr.write('expk xxx.npk\n');
    exit(1);
  }

  var keys_file = new File('key.txt');
  var keys_string = keys_file.readAsLinesSync();
  var keys = new List();
  for (var key_string in keys_string) {
    keys.add(int.parse(key_string));
  }

  var expk_filename = arguments[0];
  var expk_dirname = expk_filename.replaceAll('.npk', '');
  new Directory(expk_dirname).createSync();
  var expk_file = new File(expk_filename);
  var content = expk_file.readAsBytesSync();
  var magic_number = content.sublist(0, 4);
  var position = 0;

  if (!listEquals(magic_number, ascii.encode('EXPK'))){
    stderr.write('This is not expk file!\n');
    exit(1);
  }

  position += 4;
  
  var file_count = getUint32(content, position);
  position += 4;
  var var_1 = getUint32(content, position);
  position += 4;
  var var_2 = getUint32(content, position);
  position += 4;
  var var_3 = getUint32(content, position);
  position += 4;
  var index_offset = getUint32(content, position);
  position += 4;

  var index_table_content = content.sublist(index_offset, index_offset + file_count * 28);
  decrypt(index_table_content, keys);
  var index_table = new List();
  for (var i = 0; i < file_count; i++) {
    var index = getIndex(index_table_content, i * 28);
    index_table.add(index);
  }

  for (var i = 0; i < index_table.length; i++) {
    var index = index_table[i];
    if (index['file_length'] > keys.length){
      continue;
    }
    var item_content = content.sublist(index['file_offset'], index['file_offset'] + index['file_length']);
    decrypt(item_content, keys);
    if (index['file_flag'] != 0) {
      item_content = zlib.decode(item_content);
    }
    var ext = getExt(item_content);
    if (ext == 'none' || ext == 'dat') {
      continue;
    }
    stderr.write('${i}/${index_table.length}\n');
    var item_file = new File(expk_dirname + '/${i}.${ext}');
    item_file.writeAsBytesSync(item_content);
  }  

}