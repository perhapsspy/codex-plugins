# 기여하기

[English](CONTRIBUTING.en.md)

이 저장소는 플러그인 목록과 설치 commit만 관리합니다. 플러그인 기능, 문서와 manifest는 먼저 해당 소스 저장소에서 변경하고 검증해야 합니다.

## 고정 commit 갱신

1. 플러그인 소스 저장소의 변경을 검증하고 공개 원격에 push합니다.
2. `.agents/plugins/marketplace.json`의 `source.sha`를 그 commit의 40자리 SHA로 바꿉니다.
3. 아래 검증을 실행합니다.
4. 변경 diff에 의도한 plugin, URL, 경로와 SHA만 바뀌었는지 확인합니다.

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_marketplace.py --verify-remote
```

`--verify-remote`는 고정한 commit과 plugin 경로에서 `.codex-plugin/plugin.json`을 읽고 이름과 SemVer version을 확인합니다.

## 플러그인 추가

`.agents/plugins/marketplace.json`의 `plugins` 배열에 항목을 추가합니다. 항목 이름은 kebab-case여야 하며 같은 이름을 두 번 등록할 수 없습니다.

```json
{
  "name": "plugin-name",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/perhapsspy/plugin-name.git",
    "path": "./plugins/plugin-name",
    "sha": "0123456789abcdef0123456789abcdef01234567"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Developer Tools"
}
```

예시 SHA는 형식만 보여 줍니다. 실제 항목에는 원격에 존재하고 검증을 통과한 commit을 사용합니다. 플러그인이 저장소 루트에 있다면 현재 validator와 catalog 계약을 함께 바꾸고 그 경우를 test에 추가해야 합니다.

## 검토 기준

- marketplace 이름과 표시 이름이 `perhapsspy`, `perhapsspy Plugins`로 유지되는가
- URL이 인증 정보 없는 HTTPS Git URL인가
- 경로가 `./`로 시작하고 원격 저장소 밖을 가리키지 않는가
- full SHA가 공개 원격의 plugin manifest를 가리키는가
- policy field와 값이 Codex marketplace 계약에 맞는가
