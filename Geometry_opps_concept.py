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

# Example Usage
rectangle = Rectangle(5, 10)
print(f"Rectangle Area: {rectangle.area()}, Perimeter: {rectangle.perimeter()}, Diagonal: {rectangle.diagonal()}")

square = Square(7)
print(f"Square Area: {square.area()}, Perimeter: {square.perimeter()}")

circle = Circle(3)
print(f"Circle Area: {circle.area()}, Perimeter: {circle.perimeter()}")

sphere = Sphere(4)
print(f"Sphere Volume: {sphere.volume()}")