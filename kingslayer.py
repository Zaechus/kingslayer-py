#!/usr/bin/env python

print("\n~~ KINGSLAYER ~~\n\n"
      "Based on the original version written in Rust at "
      "https://github.com/Zaechus/kingslayer\n")


class CmdTokens:
    def __init__(self, verb="", obj="", prep="", obj_prep=""):
        self.verb = verb
        self.obj = obj
        self.prep = prep
        self.obj_prep = obj_prep

    def __str__(self):
        return (f"    verb: {self.verb}\n"
                f"     obj: {self.obj}\n"
                f"    prep: {self.prep}\n"
                f"obj_prep: {self.obj_prep}")


def filter_parts(s):
    words = s.strip().split(" ")
    map(str.lower, words)

    return [
        x for x in words if x not in [
            "a", "an", "around", "at", "of", "my", "that", "the", "through",
            "to", "'"
        ]
    ]


def mod_words(words):
    modified = list(words)

    for x in range(len(words)):
        if words[x] == "n":
            modified[x] = "north"
        elif words[x] == "s":
            modified[x] = "south"
        elif words[x] == "e":
            modified[x] = "east"
        elif words[x] == "w":
            modified[x] = "west"
        elif words[x] == "ne":
            modified[x] = "northeast"
        elif words[x] == "nw":
            modified[x] = "northwest"
        elif words[x] == "se":
            modified[x] = "southeast"
        elif words[x] == "sw":
            modified[x] = "southwest"
        elif words[x] == "u":
            modified[x] = "up"
        elif words[x] == "d":
            modified[x] = "down"
        elif words[x] == "l":
            modified[x] = "look"
        elif words[x] == "i":
            modified[x] = "inventory"

    return modified


def lex(s):
    words = mod_words(filter_parts(s))

    if len(words) == 0:
        return CmdTokens()
    elif len(words) < 2:
        return CmdTokens(words[0])
    else:
        prep_pos = [
            x for x in range(len(words))
            if words[x] in ["in", "inside", "from", "on", "with"]
        ]

        if len(prep_pos) > 0 and prep_pos[0] != 0:
            obj, obj_prep = "", ""
            if len(words[1:prep_pos[0]]) != 0:
                obj = " ".join(words[1:prep_pos[0]])

            if len(words[prep_pos[0] + 1:]) != 0:
                obj_prep = " ".join(words[prep_pos[0] + 1:])

            return CmdTokens(words[0], obj, words[prep_pos[0]], obj_prep)
        else:
            return CmdTokens(words[0], " ".join(words[1:]))


def parse(command, world, player):
    if command.verb == "help":
        return ("Commands:\n"
                "\tgo, enter <direction>\n"
                "\t<cardinal direction>\n"
                "\tl, look\n"
                "\ti, inventory\n"
                "\ttake <item>\n"
                "\tdrop <item>\n"
                "\tattack <enemy> with <item>")
    elif command.verb == "hi" or command.verb == "hello":
        return "Hello, sailor!"
    elif command.verb in [
            "north", "south", "east", "west", "northeast", "northwest",
            "southeast", "southwest", "up", "down", "go", "enter"
    ]:
        if command.obj != "":
            return world.move_room(command.obj)
        else:
            return world.move_room(command.verb)
    elif command.verb == "look":
        return world.look()
    elif command.verb == "inventory":
        return player.put_inventory()
    elif command.verb == "take":
        if command.obj != "":
            return player.take(world.give_item(command.obj))
        else:
            return "I don't know what to take!"
    elif command.verb == "drop":
        if command.obj != "":
            return world.recv_item(player.drop(command.obj))
        else:
            return "I don't know what to drop!"
    elif command.verb == "attack":
        if command.prep == "with":
            if command.obj != "":
                if command.obj_prep != "":
                    return world.harm_enemy(command.obj, command.obj_prep,
                                            player.attack(command.obj_prep))
                else:
                    return "I don't know what to attack with!"
            else:
                return "I don't know what to attack!"
        else:
            return "That doesn't make any sense."
    else:
        return "I do not understand that phrase."


class Enemy:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc
        self.hp = 10
        self.damage = 2

    def take_damage(self, damage):
        self.hp -= damage
        return f"The {self.name} screams in pain and becomes angrier."


class Item:
    def __init__(self, name, desc, damage=0):
        self.name = name
        self.desc = desc
        self.damage = damage


class Pathway:
    def __init__(self, directions, target, desc):
        self.directions = directions
        self.target = target
        self.desc = desc


class Room:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc
        self.pathways = []
        self.items = []
        self.enemies = []

    def add_pathway(self, pathway):
        self.pathways.append(pathway)

    def add_item(self, item):
        self.items.append(item)

    def add_enemy(self, enemy):
        self.enemies.append(enemy)

    def item_pos(self, item_name):
        for x in range(len(self.items)):
            if self.items[x].name == item_name:
                return x

    def enemy_pos(self, enemy_name):
        for x in range(len(self.enemies)):
            if self.enemies[x].name == enemy_name:
                return x

    def look(self):
        res = f"{self.name}\n{self.desc}"
        for p in self.pathways:
            res += "\n" + p.desc
        for i in self.items:
            res += "\n" + i.desc
        for e in self.enemies:
            res += "\n" + e.desc
        return res

    def get_pathway(self, direction):
        for p in self.pathways:
            if direction in p.directions:
                return p

    def give_item(self, item_name):
        pos = self.item_pos(item_name)
        if pos != None:
            return self.items.pop(pos)

    def recv_item(self, item):
        if item != None:
            self.items.append(item)
            return "Dropped."
        else:
            return "You do not have that item."

    def harm_enemy(self, enemy_name, damage):
        pos = self.enemy_pos(enemy_name)
        if pos != None:
            return self.enemies[pos].take_damage(damage)
        else:
            return f"There is no '{enemy_name}'"


class World:
    def __init__(self, curr_room):
        self.curr_room = curr_room
        self.rooms = {}

    def add_room(self, key, room):
        self.rooms[key] = room

    def clear_dead_enemies(self):
        res = ""
        for x in range(len(self.rooms[self.curr_room].enemies)):
            if self.rooms[self.curr_room].enemies[x].hp < 0:
                res += f"\nThe {self.rooms[self.curr_room].enemies[x].name} dies."
                self.rooms[self.curr_room].enemies.pop(x)
        return res

    def look(self):
        return self.rooms[self.curr_room].look()

    def move_room(self, direction):
        path = self.rooms[self.curr_room].get_pathway(direction)
        if path != None:
            self.curr_room = path.target
            return self.look()
        else:
            return "You cannot go that way."

    def give_item(self, item_name):
        return self.rooms[self.curr_room].give_item(item_name)

    def recv_item(self, item):
        return self.rooms[self.curr_room].recv_item(item)

    def harm_enemy(self, enemy_name, weapon_name, damage):
        if damage != None:
            return self.rooms[self.curr_room].harm_enemy(enemy_name, damage)
        else:
            return f"You do not have the '{weapon_name}'"


class Player:
    def __init__(self):
        self.hp = 10
        self.inventory = []

    def put_inventory(self):
        if len(self.inventory) > 0:
            res = "You are carrying:"
            for i in self.inventory:
                res += "\n  " + i.name
            return res
        else:
            return "Your inventory is empty."

    def item_pos(self, item_name):
        for x in range(len(self.inventory)):
            if self.inventory[x].name == item_name:
                return x

    def take(self, item):
        if item != None:
            self.inventory.append(item)
            return "Taken."
        else:
            return "No item found."

    def drop(self, item_name):
        pos = self.item_pos(item_name)
        if pos != None:
            return self.inventory.pop(pos)

    def attack(self, item_name):
        pos = self.item_pos(item_name)
        if pos != None:
            return self.inventory[pos].damage

    def take_damage(self, enemy_name, damage):
        self.hp -= damage
        return f"The {enemy_name} hits you for {damage} damage. You have {self.hp} HP left."


world = World("Circle Room")

# Start Room
start_room = Room("Circle Room", "You stand in a circular room made of stone.")
start_room.add_pathway(
    Pathway(["north", "hallway", "opening"], "Hallway",
            "An opening to the north shows a hallway."))
start_room.add_pathway(
    Pathway(["west", "tunnel"], "Long Tunnel",
            "There is a tunnel to the west."))

# Long Tunnel
long_tunnel = Room("Long Tunnel", "You crouch in a long, dark tunnel.")
long_tunnel.add_pathway(
    Pathway(["west", "tunnel"], "Long Tunnel",
            "The tunnel continues to the west."))
long_tunnel.add_pathway(
    Pathway(["east", "light"], "Circle Room",
            "There is light coming from the east."))

# Hallway
hallway = Room("Hallway", "You are in a long thin hallway.")
hallway.add_pathway(
    Pathway(["south"], "Circle Room", "The hallway opens towards the south."))
hallway.add_pathway(
    Pathway([
        "north",
    ], "Mud Room",
            "There is a dirty smell coming from the path to the north."))

hallway.add_item(Item("sword", "There is a sword here.", 5))

# Mud Room
mud_room = Room("Mud Room",
                "You stand knee deep in a room of mud. It's hard to move.")
mud_room.add_pathway(
    Pathway(["south", "hallway"], "Hallway",
            "There is a hallway to the south."))

mud_room.add_enemy(
    Enemy("pig", "There is a pig here; it snorts angrily at you."))

world.add_room("Circle Room", start_room)
world.add_room("Long Tunnel", long_tunnel)
world.add_room("Hallway", hallway)
world.add_room("Mud Room", mud_room)

player = Player()

print("Use 'help' if you get confused.\n")

print(parse(CmdTokens("look"), world, player))

while True:
    command = lex(input("\n> "))

    res = parse(command, world, player)

    events = ""

    events += world.clear_dead_enemies()
    for e in world.rooms[world.curr_room].enemies:
        events += "\n" + player.take_damage(e.name, e.damage)

    print(res, events)

    if player.hp <= 0:
        print("You died.")
        break

    if "dies" in events:
        print("You win!")
        break
