# HELLSCRIPT Web

[게임 플레이 / Play](https://dakrdong.github.io/HELLSCRIPT-Web/)

브라우저에서 실행하는 HELLSCRIPT의 게스트 버전입니다. 진행 상황은 현재 브라우저에 저장됩니다. 브라우저 데이터를 삭제하면 저장도 삭제됩니다. 다른 탭으로 이동하면 사냥이 일시정지됩니다. Google 로그인과 기기 간 저장 동기화는 제공하지 않습니다.

This is the browser guest edition of HELLSCRIPT. Progress is saved in this browser. Clearing browser data deletes your save. Hunting pauses when you leave the tab. Google sign-in and cross-device synchronization are not included.

## 배포 / Deployment

이 저장소에는 실행용 웹 빌드와 배포 도구만 담습니다. GitHub Actions가 파일 조각의 SHA-256을 검사하고 원래 Unity 빌드로 복원한 뒤 GitHub Pages에 게시합니다. 브라우저에는 복원된 게임 파일이 전달됩니다.

빌드 기준 커밋과 파일 해시는 `player/manifest.json` 및 공개 사이트의 `build-info.json`에서 확인할 수 있습니다. 로컬에서 실행하려면 `python3 assemble_web.py assemble player _site`로 복원한 뒤 `_site`를 HTTP 서버로 제공합니다.

This repository contains the executable player export and deployment tooling. GitHub Actions verifies every chunk by SHA-256, reconstructs the Unity Web build and deploys it to GitHub Pages. Chunks keep each Git object below GitHub's file limit. The browser receives the original player files.

The build revision and file hashes are available in `player/manifest.json` and on the deployed site's `build-info.json`. Do not serve the chunk folder directly: use the Pages workflow or run `python3 assemble_web.py assemble player _site` and serve `_site` over HTTP.

[개발 기록 / Development record](https://dakrdong.github.io/HELLSCRIPT-Wiki/#/page/web-build)
