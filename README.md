# AoC Telegram Notifier Bot

Notifier bot for Telegram Messenger. 
Monitors change in a private leaderboard at https://adventofcode.com/. Send updates to telegram chats.

#### How to Run

We do not publish docker images, so you should build it by yourself

1. Clone repository

    ```shell script
    git clone git@github.com:vlad-tokarev/aoc-telegram-bot.git
    cd aoc-telegram-bot
    ```

2. Build docker
    ```shell script
    make docker-build
    ```

3. Prepare configuration

    Create `.env` in the root of repo 
    ```shell script
    touch .env
    ```
    
    Set `aoc_bot__aoc_leader_board_url` variable to URL of your private leaderboard that should be monitored. 
    Replace YEAR by competition year and BOARD_ID by your private leaderboard id.
    You can just open leaderboard in your web browser and copy link from there.
     ```shell script
    echo 'aoc_bot__aoc_leader_board_url=https://adventofcode.com/YEAR/leaderboard/private/view/BOARD_ID' >> .env
     ```
    
    Set `aoc_bot__telegram_chats` to telegram chat ids where bot should send notifications.
    To get chat id you can use different methods. 
    Check https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id
    Attention: your telegram bot should be added to these chats.
     ```shell script
    echo 'aoc_bot__telegram_chats=["640247566", "421251151"]' >> .env
     ```
   
   For other configuration parameters check `Settings` model in `aoc_bot/models.py`
   
4. Prepare secrets

    Create directory with secrets 
    ```shell script
    mkdir .local_secrets
    export SECRETS_DIR=$PWD/.local_secrets
    ```
   
   Create `aoc_bot__aoc_session_id` with session_id from cookie at `https://adventofcode.com/`. 
   You can grab it in dev-tools. Unfortunately there are no different ways to authenticate. But the
   expiration of session_id is one month. So no worry. It's enough to finish one year competition.
   ```shell script
   echo <your-session-id> > $SECRETS_DIR/aoc_bot__aoc_session_id 
   ```
   
   Create `aoc_bot__telegram_token` with telegram bot token. 
   Check how to get it: https://core.telegram.org/bots#6-botfather
   ```shell script
   echo <your-telegram-bot-token> > $SECRETS_DIR/aoc_bot__telegram_token 
   ```


Run docker
```shell script
docker run --env-file=.env -v $SECRETS_DIR:/run/secrets aoc-telegram-bot:latest
```

   
#### How to contribute

Please make lint and test check before submitting PR.
Take into account that some tests are integration tests and require a configuration.
```shell script
make lint
make test
```

#### Kubernetes

You can find example of Kubernetes `Deployment` in the `./deploy` folder. 

#### QA

**Where should I get telegram chat id?**

Check https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id


**Why bot is unable to find chat id by itself?**

The main goal is keep bot codebase as much simple as possible. We do not keep any state. We do not use database.
For example previous leaderboard to compare with current is just stored in process memory.
This is why we require that user configure chat ids by himself.


