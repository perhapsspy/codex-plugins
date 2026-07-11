# AGENTS.md

- 일반 문서는 한국어로 작성하고 `README.md`와 `CONTRIBUTING.md`를 바꾸면 영어 pair도 함께 갱신한다.
- 이 저장소는 marketplace metadata와 검증만 소유한다. 플러그인 구현은 각 `source.url` 저장소에서 변경한다.
- `source.sha`에는 공개 원격에 존재하는 40자리 commit SHA만 넣고 branch나 tag를 사용하지 않는다.
- 플러그인을 추가하거나 pin을 바꾼 뒤 원격 manifest 검증까지 실행한다.

## 검증

- `python3 -m unittest discover -s tests -p 'test_*.py' -v`
- `python3 scripts/validate_marketplace.py --verify-remote`
