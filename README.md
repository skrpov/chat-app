# What 

Chat app to learn django websockets / channels fundamental for a more interesting project.

# Building

- Docker version >= 20

```sh
docker compose up --build
```


# Scope 
- Have users
- Have rooms, maybe with the rooms having permissions
- Have a telegram-like UI for choosing rooms 
- Have and a quick and dirty login flow 
- Have some kind of messsage types, maybe implement a "read" indicator since a real chat app would need something like this.

![Flow diagram](<docs/flow_diagram.png>)

# Tasks 
- [x] Make messages persist
- [x] Make sure that the client is able to view room history, not just the newest messages
    - [ ] Send only a most recent window of history, and send more on request.
- [ ] Dockerize the application and add running instructions
- [ ] Ensure that on the client messages appear in the same order they were sent in
- [x] Make messages send to all connections, not just the sender.
- [ ] Add authentication
    - [ ] Add a way to signup
    - [ ] Add a way to login
    - [ ] Ensure that pages other then login and signup redirect on unauthenticated access
- [ ] Add rooms 
- [ ] Add room permissions
    - [ ] Owners can own a room
    - [ ] Rooms can be made public
        - [ ] Room owner can add other users to a blacklist
    - [ ] Rooms can be made private
      - [ ] Room owner can add other users to a whitelist
