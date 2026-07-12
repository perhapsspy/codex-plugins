# perhapsspy 플러그인

[English](README.en.md)

perhapsspy가 공개하는 플러그인을 설치하고 업데이트하기 위한 marketplace입니다. 각 제품의 설명과 변경 내역은 연결된 저장소에서 확인할 수 있습니다.

## 설치

마켓플레이스는 한 번만 등록하면 됩니다.

```bash
codex plugin marketplace add perhapsspy/codex-plugins
```

필요한 플러그인을 설치합니다.

```bash
codex plugin add project-legibility@perhapsspy
```

## 플러그인

| 이름 | 설치 | 제품 문서 |
|---|---|---|
| Project Legibility | `codex plugin add project-legibility@perhapsspy` | [perhapsspy/project-legibility](https://github.com/perhapsspy/project-legibility) |

## 업데이트와 제거

```bash
# 마켓플레이스 목록 갱신
codex plugin marketplace upgrade perhapsspy

# 카탈로그가 가리키는 버전으로 다시 설치
codex plugin add project-legibility@perhapsspy

# 플러그인 제거
codex plugin remove project-legibility@perhapsspy
```

등록한 마켓플레이스도 지우려면 플러그인을 제거한 뒤 다음 명령을 실행합니다.

```bash
codex plugin marketplace remove perhapsspy
```

## 관리

카탈로그를 바꾸는 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)에 있습니다. 모든 원격 플러그인은 branch나 tag 대신 전체 commit SHA로 고정하며, CI에서 해당 경로의 manifest를 확인합니다.

## 라이선스

[MIT](LICENSE)
