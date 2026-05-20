def read_jsonl(file_path):
    data = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as error:
                    print(f"[JSONL 오류] {line_number}번째 줄을 읽을 수 없습니다: {error}")

    except FileNotFoundError:
        print(f"[파일 오류] 파일을 찾을 수 없습니다: {file_path}")

    except PermissionError:
        print(f"[파일 오류] 파일 접근 권한이 없습니다: {file_path}")

    except OSError as error:
        print(f"[파일 오류] 파일을 읽는 중 문제가 발생했습니다: {error}")

    return data