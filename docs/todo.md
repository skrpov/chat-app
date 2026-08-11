# Tasks

An index into the GitHub issues, which hold the descriptions and any notes on what
was actually implemented. Git history is authoritative on what is done.

## Messaging

- [x] Make messages persist
- [x] Make sure that the client is able to view room history, not just the newest messages
    - [x] Send only a most recent window of history, and send more on request.
- [x] Ensure that on the client messages appear in the same order they were sent in
- [x] Make messages send to all connections, not just the sender.
- [x] Add a placeholder for when a room has no messages
- [x] Add join notification message
- [x] Add re-connect behaviour in case of browser closing the connection or server dropping or else.
- [ ] Show profile pictures in the chat view
    - [ ] Send the sender's user id in the message packet
    - [ ] Take the display name from the authenticated user instead of the client packet
    - [ ] Render the avatar beside each message, falling back to the initial placeholder
    - [ ] Test the app still works end-to-end on dev server
    - [ ] Deploy profile pictures in chat to live server
- [ ] Rate limiting and spam protection
    - [ ] Limit how often one connection can send messages
    - [ ] Enforce the message length limit in the consumer
    - [ ] Throttle signup and login attempts
- [ ] Add some kind of message encryption / hashing
- [ ] Add a "delievered" indicator
- [ ] Add a "read" indicator
- [ ] Only new message send time when the time is significantly different
- [ ] Add image sending support (long-term)
- [ ] Bug: every message send runs a COUNT over the whole room
- [ ] Bug: the chat view loads every message in the database into a context the template never uses

## Rooms

- [x] Add rooms
    - [x] No rooms yet placeholder
    - [x] Switching rooms closes the connection to current room before opening another
    - [x] Adding a new room makes it correctly show up in the room list
    - [x] Selected room is highlighted in the room list
    - [x] Room list order is sorted
    - [x] Room settings are only visible to room owner
    - [x] Room name correctly shows up in the chat view
    - [x] Navigating to a room that isn't saved saves that room for the user.
    - [ ] Room name can be changed.
    - [ ] User can un-save a room
- [x] Add room permissions
    - [x] Owners can own a room
    - [x] Rooms can be made public
        - [x] Room owner can add other users to a blacklist
    - [x] Rooms can be made private
        - [x] Room owner can add other users to a whitelist
- [x] Make the room sidebar resizable / collapsible (mobile support)
- [x] Add hamburger menu for group list page s.t. the chat is more usable on mobile.
- [ ] Room visibility levels
    - [ ] Replace public and private with viewable by anyone, signed-in users, or invite only
        - [ ] Migrate existing rooms onto the new levels
        - [ ] Split the access check into view and post
        - [ ] Handle anonymous users in the access check
        - [ ] Update the room settings UI for the third level
    - [ ] Let anonymous users read rooms that anyone can view
        - [ ] Serve the chat view without requiring login for those rooms
        - [ ] Skip saving the room for anonymous visitors
        - [ ] Accept read-only websocket connections
        - [ ] Reject sends from anonymous users and prompt account creation
        - [ ] Handle the sidebar and header with no logged in user
- [ ] Explore and search
    - [ ] Search rooms by name or id
    - [ ] Explore page listing rooms that anyone can view
    - [ ] Onboarding path from a room into signup
- [ ] Show current room name in the browser tab title

## Accounts

- [x] Add authentication
    - [x] Add a way to signup
    - [x] Add a way to login
    - [x] Ensure that pages other then login and signup redirect on unauthenticated access
    - [x] Display logged in user name in chat UI
- [x] Add profile pictures
- [ ] Fix user signup flow
    - [ ] Add email field to signup
        - [ ] Need to delete old accounts that have no recovery method.
        - [ ] Create django admin account to make sure that there are no real accounts to delete
        - [ ] Fix the broken form behaviour with clearing fields on error
        - [ ] Update form to require email
        - [ ] Create migration deleting no-email accounts
        - [ ] Test the app still works end-to-end on dev server
        - [ ] Deploy email signup update to live server
    - [ ] Add account recovery via email
        - [ ] Add email delivery provider
            - [ ] Signup for Resend
            - [ ] Hook up resend to django mail backend
            - [ ] Add SPF, DKIM and DMARC records for the sending domain
        - [ ] Enable the django password reset routes
        - [ ] Style the reset pages and emails to match the app
        - [ ] Test a full reset against a real address
    - [ ] Add signup with Google option
        - [ ] Register for the service in Google cloud console
        - [ ] Add django-allauth and configure the provider
        - [ ] Decide what happens when a Google address matches an existing account

## Notifications

- [ ] Decide where a notification lives while the user is offline
- [ ] Deliver notifications over the existing websocket
- [ ] Send someone a room link without already sharing a room

## UI

- [x] Add app icon (favicon)
- [x] Add a landing page instead of just redirecting to login page right off the bat.
- [ ] UI rework
    - [ ] Restyle so the app does not read as default Bootstrap
    - [ ] Dark mode / Global styles

## Bots and demo traffic

- [ ] Script that signs up, logs in and drives a websocket
- [ ] Run it against a local container rather than the live server
- [ ] Chess bot that plays in its own room

## Infrastructure

- [x] Dockerize the application and add running instructions
- [x] Host the messenger
- [ ] Move to carrierpigeon.app
    - [ ] Register the domain
    - [ ] Point DNS at the VM
    - [ ] Update the Caddyfile for the new domain
    - [ ] Update ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
    - [ ] Verify TLS is issued on the new domain
    - [ ] Redirect the duckdns domain at the new one
- [ ] Move the database to Postgres
- [ ] Move the VM to Debian trixie and update the Dockerfile base
- [ ] Secure redis so that it does not accept connections from other sources.
- [ ] Database backups
- [ ] Document the venv as editor support only
- [ ] Register the chat and accounts models in the django admin
- [ ] Bug: `scripts/setup.sh` creates the venv with `python3` rather than `python3.12`
