import math

class Shape:  # Base class (optional)
    def area(self):
        pass

    def perimeter(self):
        pass

class Rectangle(Shape):
    def __init__(self, length, width):
        if length < 0 or width < 0:
            raise ValueError("Length and width must be non-negative.")
        self.length = length
        self.width = width

    def area(self):
        return self.length * self.width

    def perimeter(self):
        return 2 * (self.length + self.width)

    def diagonal(self):
        return math.sqrt(self.length**2 + self.width**2)

class Square(Rectangle): # Inherits from Rectangle
    def __init__(self, side):
        super().__init__(side, side)

class Circle(Shape):
    def __init__(self, radius):
        if radius < 0:
            raise ValueError("Radius must be non-negative.")
        self.radius = radius

    def area(self):
        return math.pi * self.radius**2

    def perimeter(self):
        return 2 * math.pi * self.radius

class Sphere:
    def __init__(self, radius):
        if radius < 0:
            raise ValueError("Radius must be non-negative.")
        self.radius = radius

    def volume(self):
        return (4/3) * math.pi * self.radius**3

"""Cube	Cuboid
Total Surface Area = 6(side)2	Total Surface area = 2 (length × breadth + breadth × height + length × height)
Lateral Surface Area = 4 (Side)2	Lateral Surface area = 2 height(length + breadth)
Volume of cube = (Side)3	Volume of the cuboid = (length × breadth × height)"""


class Cube:
    def __init__(self, length):
        if length < 0:
            raise ValueError("Length must be non-negative.")
        self.__length = length  # Private attribute

    def total_surface_area(self):
        return self.__length**2 * 6

    def volume(self):
        return self.__length**3

    # Getter method for length
    def get_length(self):
        return self.__length

    # Setter method for length (with validation)
    def set_length(self, length):
        if length >= 0:
            self.__length = length
        else:
            print("Invalid length.")

class Cuboid:
    def __init__(self, length, breadth, height):
        if length < 0 or breadth < 0 or height < 0:
            raise ValueError("Dimensions must be non-negative.")
        self.__length = length  # Private attributes
        self.__breadth = breadth
        self.__height = height

    def total_surface_area(self):
        return 2 * (self.__length * self.__breadth + self.__breadth * self.__height + self.__length * self.__height)

    def volume(self):
        return self.__length * self.__breadth * self.__height

    # Getter methods
    def get_length(self):
        return self.__length

    def get_breadth(self):
        return self.__breadth

    def get_height(self):
        return self.__height

    # Setter methods (with validation)
    def set_length(self, length):
        if length >= 0:
            self.__length = length
        else:
            print("Invalid length.")

    def set_breadth(self, breadth):
        if breadth >= 0:
            self.__breadth = breadth
        else:
            print("Invalid breadth.")

    def set_height(self, height):
        if height >= 0:
            self.__height = height
        else:
            print("Invalid height.")




# Example Usage
rectangle = Rectangle(5, 10)
print(f"Rectangle Area: {rectangle.area()}, Perimeter: {rectangle.perimeter()}, Diagonal: {rectangle.diagonal()}")

square = Square(7)
print(f"Square Area: {square.area()}, Perimeter: {square.perimeter()}")

circle = Circle(3)
print(f"Circle Area: {circle.area()}, Perimeter: {circle.perimeter()}")

sphere = Sphere(4)
print(f"Sphere Volume: {sphere.volume()}")
