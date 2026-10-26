# Форк ppt-master для preza

Ветка `preza` — релиз [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) плюс правки для плагина [preza](https://github.com/Inhibit0r/preza): указатели на правила `preza:deck-house-rules`, проверка контракта и автосинхронизация. preza ставит отсюда `ppt-master@preza`; ветка `main` форка не используется.

## Синхронизация

`.github/workflows/sync-upstream.yml` раз в сутки (04:17 UTC) и вручную:

1. **merge** (только чтение): последний тег `vX.Y.Z` upstream; уже влит — `noop`; иначе `git merge --no-edit`, конфликт — `conflict`; затем `pip install -r requirements.txt` и `python tools/preza_contract.py --check --smoke`, красный — `contract`.
2. **push** (запись, код upstream не исполняет): повторяет слияние, сверяет дерево с проверенным и пушит fast-forward в `preza`.
3. **report**: неуспех — issue `sync <ветка> <тег>: <итог>` (повтор — комментарий в том же issue); успех — закрывает открытые issue этой ветки.

Любой отказ оставляет `preza` на прежнем коммите. Следим за релизами-тегами, поэтому форк отстаёт от `main` upstream до следующего релиза.

Ручной запуск: `gh workflow run sync-upstream.yml -f tag=v6.7.3 -f target_branch=<ветка>`.

## Восстановление

- **conflict** — слить тег локально, разрешить конфликт (обычно строки-указатели), прогнать `python tools/preza_contract.py --check --smoke`, запушить `preza`.
- **contract** — upstream изменил то, на что опирается preza: поправить preza или контракт, затем перезапустить workflow.
- **push-failed** — чаще всего upstream добавил файлы в `.github/workflows/` (у `GITHUB_TOKEN` нет права workflows): слить и запушить локально.
- Расписание выключается GitHub через 60 дней без активности репозитория: `/preza:setup` показывает дату последнего успешного прогона; включить — `gh workflow enable sync-upstream.yml`.
