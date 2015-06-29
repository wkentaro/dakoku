# dakoku

## setup

1. edit `config.sample`, rename it to `config.json`

2. edit `schedule.json`

3. execute

```bash
npm install -g pm2
cd /path/to/dakoku
pm2 start app.js --name "dakoku"
```

4. stop

```bash
pm2 stop dakoku
```
