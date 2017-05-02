import random

state_search_food = 'search some yummy'
state_hunting = 'hunting'

state_search_mate = 'search your special someone'
state_mating = 'wild se... love!'

state_died = 'good night, sweet prince...'

type_predator = 'predator'
type_prey = 'prey'


def sign(num):
    return 1 if num > 0 else -1


class Animal:
    def __init__(self, x, y, size=1):
        self.x = x
        self.y = y
        self.state = state_search_food
        self.world_size = size

        self.life = None
        self.cool_down = None
        self.vision_range = None

    def meta_tick(self):
        self.life -= 1
        if self.life == 0:
            return self.die()

        if self.cool_down > 0:
            self.cool_down -= 1

    def die(self):
        self.state = state_died

    def get_dist(self, a):
        return ((self.x - a.x) ** 2 + (self.y - a.y) ** 2) ** 0.5

    def find_nearest_animals(self, world):
        predator = None
        dist_predator = world.size

        prey = None
        dist_prey = world.size

        for a in world.predators:
            d_a = self.get_dist(a)
            if d_a < self.vision_range and d_a < dist_predator:
                dist_predator = d_a
                predator = a

        for a in world.preys:
            d_a = self.get_dist(a)
            if d_a < self.vision_range and d_a < dist_prey:
                dist_prey = d_a
                prey = a

        return predator, prey

    def go_to(self, a):
        delta_x = a.x - self.x
        if delta_x != 0:
            self.x += sign(delta_x)
            return

        delta_y = a.y - self.y
        if delta_y != 0:
            self.y += sign(delta_y)
            return

        # two animals stand at same point
        raise Exception('Impossibru!', self, a)

    def go_away_from(self, a):
        ghost = Animal(random.randint(0, self.world_size), random.randint(0, self.world_size))

        if a is not None:
            delta_x = a.x - self.x
            if delta_x != 0:
                ghost.x = self.x - sign(delta_x)
                return self.go_to(ghost)

            delta_y = a.y - self.y
            if delta_y != 0:
                ghost.y = self.y - sign(delta_y)
                return self.go_to(ghost)

            raise Exception('Impossibru!', self, a)

        return self.go_to(ghost)


class Predator(Animal):
    def __init__(self, x, y, size=1):
        super().__init__(x, y, size)
        self.life = 100
        self.cool_down = 20
        self.vision_range = 4

        self.hunt_object = None

    def tick(self, world):
        self.meta_tick()

        if self.state == state_died:
            return self.state

        elif self.state == state_hunting:
            self.go_to(self.hunt_object)

            if self.get_dist(self.hunt_object) < 2:
                self.hunt_object.die()
                self.hunt_object = None
                self.life += 30
                self.state = state_search_food

            return

        mate, prey = self.find_nearest_animals(world)
        if self.life > 50:
            if self.cool_down == 0:
                self.state = state_search_mate
        else:
            self.state = state_search_food

        if self.state == state_search_food:
            if prey is not None:
                self.state = state_hunting
                self.hunt_object = prey
                self.go_to(self.hunt_object)
                return
            else:
                self.go_away_from(mate)

        if self.state == state_search_mate:
            if mate is not None:
                self.go_to(mate)
            else:
                self.go_away_from(None)

        elif self.state == state_mating:
            # todo: creating new baby predator and adding to list
            pass

        return 1


class Prey(Animal):
    def __init__(self, x, y, size=1):
        super().__init__(x, y, size)
        self.life = 150
        self.cool_down = 15
        self.vision_range = 3

        self.hunter = None

    def tick(self, world):
        self.meta_tick()

        if self.state == state_died:
            return self.state

        predators, mate = self.find_nearest_animals(world)
        if self.life > 50:
            if self.cool_down == 0:
                self.state = state_search_mate
        else:
            self.state = state_search_food

        if self.state == state_search_food:
            # todo: продумать механизм естественной смерти травоядных
            #
            self.life += 1
            self.go_away_from(mate)

        if self.state == state_search_mate:
            if mate is not None:
                self.go_to(mate)
            else:
                self.go_away_from(None)

        pass


class World:
    def create_spawn_zones(self, spawn_center, count):
        spawn_x = spawn_center[0]
        spawn_y = spawn_center[1]

        min_x = max(0, spawn_x - self.spawn_area_size)
        max_x = min(self.size, spawn_x + self.spawn_area_size)

        min_y = max(0, spawn_y - self.spawn_area_size)
        max_y = min(self.size, spawn_y + self.spawn_area_size)

        spawn = []
        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                spawn.append([x, y])

        out = []
        for i in range(count):
            spawn_point = random.choice(spawn)
            out.append(spawn_point)
            spawn.remove(spawn_point)

        return out

    def __init__(self, spawn_area, size, predators_count, preys_count):
        self.spawn_area_size = spawn_area
        self.size = size

        predators_zone = [random.randint(0, size), random.randint(0, size)]
        self.predators = [Predator(p[0], p[1], size) for p in
                          self.create_spawn_zones(predators_zone, predators_count)]

        preys_zone = [random.randint(0, size), random.randint(0, size)]
        self.preys = [Prey(p[0], p[1], size) for p in self.create_spawn_zones(preys_zone, preys_count)]
        return

    def world_tick(self):
        for prey in self.preys:
            out = prey.tick(self)

        for predator in self.predators:
            out = predator.tick(self)


spawn_area_size = 3
world_size = 20
w = World(spawn_area_size, world_size, 5, 10)

# todo: !!! https://en.wikipedia.org/wiki/Lotka–Volterra_equations
# 1. The prey population finds ample food at all times.
# 2. The food supply of the predator population depends entirely on the size of the prey population.
# 3. The rate of change of population is proportional to its size.
# 4. During the process, the environment does not change in favour
#    of one species and genetic adaptation is inconsequential.
#
# 5. Predators have limitless appetite.
