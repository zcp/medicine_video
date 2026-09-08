import csv


def convert_experts_csv_robust(input_path, output_path):
    """
    健壮的 CSV 转换：处理复杂格式
    """
    # 尝试多种编码
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'gb18030']
    content = None
    used_encoding = None

    for encoding in encodings:
        try:
            with open(input_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            used_encoding = encoding
            print(f"✓ 使用 {encoding} 编码读取文件")
            break
        except Exception as e:
            continue

    if content is None:
        raise ValueError("❌ 无法读取文件")

    # 移除 BOM
    content = content.lstrip('\ufeff')

    # 尝试检测分隔符
    first_line = content.split('\n')[0]
    if '\t' in first_line:
        delimiter = '\t'
        print(f"✓ 检测到 Tab 分隔符")
    else:
        delimiter = ','
        print(f"✓ 检测到逗号分隔符")

    # 解析 CSV
    lines = content.splitlines()
    reader = csv.reader(lines, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)

    rows = []
    for i, row in enumerate(reader):
        if i == 0:
            # 表头
            print(f"✓ 检测到 {len(row)} 列")
            print(f"  列名: {', '.join(row[:5])}...")

            # 验证必需列
            if 'name' not in row:
                raise ValueError(f"❌ 缺少必需列 'name'，当前列: {row}")

            rows.append(row)
        else:
            # 数据行：仅去除首尾空白，保留列内换行与多空格（仍属一列）
            cleaned_row = [
                field.strip() if isinstance(field, str) else field
                for field in row
            ]
            rows.append(cleaned_row)

    # 写入标准 CSV：逗号分隔；含换行/逗号/空格的列自动加双引号，保证一列即一列
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(
            f,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator='\n',
        )
        writer.writerows(rows)

    print(f"\n✓ 转换完成！")
    print(f"  输入: {input_path}")
    print(f"  输出: {output_path}")
    print(f"  总行数: {len(rows) - 1} (不含表头)")

    # 验证输出
    with open(output_path, 'r', encoding='utf-8-sig') as f:
        verify_reader = csv.DictReader(f)
        first_row = next(verify_reader, None)
        if first_row:
            print(f"\n验证第一行数据:")
            print(f"  name: {first_row.get('name', 'N/A')}")
            print(f"  title: {first_row.get('title', 'N/A')}")
            print(f"  hospital: {first_row.get('hospital', 'N/A')}")


if __name__ == "__main__":
    input_file = r"D:\项目\陶伟\video_website\experts.csv"
    output_file = r"D:\项目\陶伟\video_website\experts_cleaned.csv"

    try:
        convert_experts_csv_robust(input_file, output_file)
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        import traceback

        traceback.print_exc()