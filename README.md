# dakoku

## setup

0. execute setup script

```bash
./install.sh
```

1. edit `config.sample`, then rename it to `config.json`

2. edit `schedule.sample`, then rename it to `schedule.json`

3. execute

```bash
pm2 start pm2.json # launch as daemon
```

4. register as permanent node

```bash
pm2 startup pm2.json
```
5. stop

```bash
pm2 stop dakoku
```
