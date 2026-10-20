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
codex plugin add chatgpt-pro-reasoner@perhapsspy
```

## Claude Code 게시

Project Legibility의 동시 지원 release가 `.claude-plugin/marketplace.json`을 생성하고 Codex catalog와 같은 release commit을 고정합니다. 해당 catalog 게시 뒤 다음 명령을 사용합니다.

```bash
claude plugin marketplace add perhapsspy/codex-plugins
claude plugin install project-legibility@perhapsspy
```

Publisher validator는 source identity·SHA의 일치와 고정된 `.claude-plugin/plugin.json`을 확인합니다. Claude catalog에는 등록된 플러그인만 노출합니다.

## 플러그인

| 이름 | 설치 | 제품 문서 | 변경 내역 |
|---|---|---|---|
| Project Legibility | `codex plugin add project-legibility@perhapsspy` | [소개와 사용법](https://github.com/perhapsspy/project-legibility#readme) | [릴리스 노트](https://github.com/perhapsspy/project-legibility/blob/main/CHANGELOG.md) |
| ChatGPT Pro Reasoner | `codex plugin add chatgpt-pro-reasoner@perhapsspy` | [소개와 사용법](https://github.com/perhapsspy/chatgpt-pro-reasoner#readme) | — |

## 업데이트와 제거

```bash
# 마켓플레이스 목록 갱신
codex plugin marketplace upgrade perhapsspy

# 카탈로그가 가리키는 버전으로 다시 설치
codex plugin add project-legibility@perhapsspy
codex plugin add chatgpt-pro-reasoner@perhapsspy

# 플러그인 제거
codex plugin remove project-legibility@perhapsspy
codex plugin remove chatgpt-pro-reasoner@perhapsspy
```

등록한 마켓플레이스도 지우려면 플러그인을 제거한 뒤 다음 명령을 실행합니다.

```bash
codex plugin marketplace remove perhapsspy
```

## 관리

플러그인 기능, 문서와 manifest는 소스 저장소에서 먼저 변경하고 공개한 뒤, 이 카탈로그에는 해당 commit의 전체 SHA를 고정합니다. Project Legibility pin은 그 저장소의 `scripts/release.py publish`가 양쪽 catalog 갱신과 검증을 소유하므로 수동으로 다시 처리하지 않습니다. 다른 catalog 변경은 다음 검증을 실행합니다.

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_marketplace.py --verify-remote
```

## 라이선스

[MIT](LICENSE)
