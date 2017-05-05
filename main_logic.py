import random
import json

state_search_food = 'search_food'
state_hunting = 'hunting'
state_search_mate = 'search_mate'
state_mating = 'mating'
state_died = 'died'


def sign(num):
    return 1 if num > 0 else -1


class Animal:
    def __init__(self, world, x, y, params: dict = None):
        self.id = world.generate_id()
        self.world = world

        self.x = x
        self.y = y
        self.state = state_search_food

        self.default_life = params['life']
        self.life_leaking_per_tick = params['life_leaking']

        self.mating_timeout = params['mating_timeout']
        self.mating_hp_border = params['mating_hp_border']

        self.vision_range = params['vision_range']
        self.meal_hp = params['meal_hp']
        self.step = params['step']
        self.type = params['type']

        self.hp = self.default_life
        self.mating_cool_down = self.mating_timeout
        self.mate: Animal = None

        self.go_x = 0
        self.go_y = 0

    def meta_tick(self):
        self.hp -= self.life_leaking_per_tick
        if self.hp <= 0:
            return self.die()

        if self.mating_cool_down > 0:
            self.mating_cool_down -= 1

    def free_and_ready_to_mate(self):
        return self.mating_cool_down == 0 and self.hp > self.mating_hp_border and self.mate is None

    def mating_actions(self):
        if not self.free_and_ready_to_mate():
            return False

        if self.mate is None:
            self.state = state_search_mate
            self.mate = self.find_nearest_mate()

        if self.state == state_search_mate:
            if self.mate is not None:
                if self.mate.free_and_ready_to_mate():
                    self.state = state_mating
                    self.mate.state = state_mating
            else:
                return False

        if self.state == state_mating:
            if self.mate.state == state_died:
                self.state = state_search_mate
                return False

            self.set_destination(self.mate.x, self.mate.y)

        if self.get_dist(self.mate) < 2 and self.mate.free_and_ready_to_mate:
            return True

    def die(self):
        self.state = state_died

    def get_dist(self, a):
        return ((self.x - a.x) ** 2 + (self.y - a.y) ** 2) ** 0.5

    def find_nearest_mate(self):
        return self.find_nearest_animal(self.type)

    def find_nearest_animal(self, animal_type: str):
        animal = None
        dist = self.world.size

        # fixme: if someone won't fix it, in future, some 'wolves' (predator) and 'foxes' (predator) can make babies
        # but now I only have one type of predator and prey
        # so, problem isn't important :D
        if animal_type == 'predator':
            l = self.world.predators
        else:
            l = self.world.preys

        for a in l:
            if a.id != self.id:
                d_a = self.get_dist(a)
                if d_a < self.vision_range and d_a < dist:
                    dist = d_a
                    animal = a

        return animal

    def go_away_from(self, a):
        if a.x == self.x and a.y == self.y:
            return self.go_to_random_place()

        x = 2 * self.x - a.x
        y = 2 * self.y - a.y
        self.set_destination(x, y)

    def go_to_random_place(self):
        x = random.randint(0, self.world.size)
        y = random.randint(0, self.world.size)
        self.set_destination(x, y)

    def set_destination(self, x, y):
        self.go_x = x
        self.go_y = y

    def go(self):
        for i in range(self.step):
            delta_x = self.go_x - self.x
            delta_y = self.go_y - self.y

            if delta_x != 0 or delta_y != 0:
                if delta_x != 0:
                    self.x += sign(delta_x)
                    continue

                if delta_y != 0:
                    self.y += sign(delta_y)
                    continue

            else:
                # self.x == x and self.y == y. we arrived the destination point
                pass

    def get_baby_coordinates(self, mate):
        return (self.x + mate.x) // 2, (self.y + mate.y) // 2

    def stats(self):
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'type': self.type,
            'life': self.hp
        }


class Predator(Animal):
    def __init__(self, world, x, y):
        params = {
            'life': 100,
            'mating_timeout': 20,
            'mating_hp_border': 60,
            'vision_range': 4,
            'life_leaking': 3,
            'meal_hp': 50,
            'step': 3,
            'type': 'predator'
        }

        super().__init__(world, x, y, params)

        self.type = 'predator'
        self.hunt_object = None

    def tick(self):
        self.meta_tick()
        if self.state == state_died:
            return None

        elif self.state == state_hunting:
            if self.hunt_object.state == state_died:
                self.hunt_object = None
                self.state = state_search_food

            elif self.get_dist(self.hunt_object) < 2:
                self.hunt_object.die()
                self.hunt_object = None
                self.hp += self.meal_hp
                self.state = state_search_food

            if self.hunt_object is not None:
                self.set_destination(self.hunt_object.x, self.hunt_object.y)
            return None

        result = self.mating_actions()
        if result:
            return self.make_new_predator()

        if self.state == state_search_food:
            prey = self.find_nearest_prey()
            if prey is not None:
                self.state = state_hunting
                self.hunt_object = prey
                self.set_destination(self.hunt_object.x, self.hunt_object.y)
            else:
                self.go_to_random_place()

        return None

    def make_new_predator(self):
        x, y = self.get_baby_coordinates(self.mate)
        return Predator(self.world, x, y)

    def find_nearest_prey(self):
        return self.find_nearest_animal('prey')


class Prey(Animal):
    def __init__(self, world, x, y):
        params = {
            'life': 50,
            'mating_timeout': 15,
            'mating_hp_border': 10,
            'vision_range': 4,
            'life_leaking': 3,
            'meal_hp': 1,
            'step': 1,
            'type': 'prey'
        }

        super().__init__(world, x, y, params)
        self.type = 'prey'

    def tick(self):
        self.meta_tick()

        if self.state == state_died:
            return None

        predator = self.find_nearest_animal('predator')
        if predator is not None:
            self.go_away_from(predator)
            return None

        result = self.mating_actions()
        if result:
            return self.make_new_prey()

        self.hp += self.meal_hp
        self.go_to_random_place()
        return None

    def make_new_prey(self):
        x, y = self.get_baby_coordinates(self.mate)
        return Prey(self.world, x, y)

    def find_nearest_prey(self):
        return self.find_nearest_animal(self.type)


class World:
    def create_spawn_zones(self, count):
        out = []
        for i in range(count):
            out.append([random.randint(0, self.size), random.randint(0, self.size)])

        return out

    def __init__(self, size, predators_count, preys_count):
        self.size = size
        self.id = 0

        self.predators = [
            Predator(self, point[0], point[1])
            for point in self.create_spawn_zones(predators_count)
        ]

        self.preys = [
            Prey(self, point[0], point[1])
            for point in self.create_spawn_zones(preys_count)
        ]

    def world_tick(self):
        for prey in self.preys:
            baby = prey.tick()
            prey.go()
            if baby is not None:
                self.preys.append(baby)

            if prey.state == state_died:
                self.preys.remove(prey)

        for predator in self.predators:
            baby = predator.tick()
            predator.go()
            if baby is not None:
                self.predators.append(baby)

            if predator.state == state_died:
                self.predators.remove(predator)

        return "predators: %d, preys: %d" % (len(self.predators), len(self.preys))

    def generate_id(self):
        self.id += 1
        return self.id

    def to_str(self) -> str:
        out = [predator.stats() for predator in self.predators]
        out.extend([prey.stats() for prey in self.preys])
        return json.dumps(out)


print('world_size, predators_c, preys_c')
world_size, predators_c, preys_c = input().split()

w = World(int(world_size), int(predators_c), int(preys_c))
f = open('data.log', 'w')
f.write(str(world_size) + '\n')

t = 0
while True:
    t += 1
    w.world_tick()
    print(t)
    txt = w.to_str() + '\n'
    if txt == '[]\n' or t > 100:
        print("%d ticks" % t)
        break

    f.write(txt)

f.close()

# todo: !!! https://en.wikipedia.org/wiki/Lotka–Volterra_equations
# 1. The prey population finds ample food at all times.
# 2. The food supply of the predator population depends entirely on the size of the prey population.
# 3. The rate of change of population is proportional to its size.
# 4. During the process, the environment does not change in favour
#    of one species and genetic adaptation is inconsequential.
#
# 5. Predators have limitless appetite.
