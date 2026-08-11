# Carrier Pigeon 🕊️

A Telegram-inspired real-time chat app built on Django Channels and WebSockets.

Live at: https://carrier-pigeon.duckdns.org 
<br><small> See [deployment plan](docs/deployment-plan.md) </small>

## Building

- Docker version >= 20

```sh
docker compose up --build
```

## Scope 
- Have users
- Have rooms, maybe with the rooms having permissions
- Have a telegram-like UI for choosing rooms 
- Have and a quick and dirty login flow 
- Have some kind of messsage types, maybe implement a "read" indicator since a real chat app would need something like this.

![Flow diagram](<docs/flow_diagram.png>)

## Tasks

<small> See [tasks](docs/todo.md) </small>


## References
- https://www.w3schools.com/django/index.php
- https://www.geeksforgeeks.org/python/learn-to-use-websockets-with-django/
- https://channels.readthedocs.io/en/latest/tutorial/part_2.html
- https://www.docker.com/blog/how-to-dockerize-django-app/
- https://github.com/jpadilla/django-project-template/blob/master/.gitignore

<small> See [reading list](docs/reading-list.md) </small>