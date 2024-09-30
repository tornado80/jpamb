from dataclasses import dataclass
from typing import TypeAlias, Literal
from hypothesis import given
from hypothesis.strategies import sets, integers

Sign : TypeAlias = Literal["+"] | Literal["-"] | Literal["0"]

@dataclass
class SignHelper:
    sign: Literal["+"] | Literal["-"] | Literal["0"]

    def __eq__(self, other):
        return self.sign == other.sign

    def __hash__(self):
        return hash(self.sign)

    def __le__(self, other):
        if self.sign == "0" and other.sign == "0":
            return {True}
        if self.sign == other.sign:
            return {True, False}
        if self.sign == "0" and other.sign == "+":
            return {True}
        if self.sign == "-" and other.sign == "+":
            return {True}
        if self.sign == "-" and other.sign == "0":
            return {True}
        return {False}

@dataclass
class SignSet:
    signs : set[Sign]

    # & = intersection of sets (meet)
    def __and__(self, other):
        return SignSet(signs = self.signs & other.signs)

    # | = union of sets (join)
    def __or__(self, other):
        return SignSet(signs = self.signs | other.signs)

    # <= = subset of sets (partial order)
    def __le__(self, other):
        return self.signs <= other.signs
    
    # + = addition of 
    def __add__(self, other):
        result = set()
        for sign1 in self.signs:
            for sign2 in other.signs:
                if sign1 == sign2:
                    result.add(sign1)
                elif sign1 == "0":
                    result.add(sign2)
                elif sign2 == "0":
                    result.add(sign1)
                else:
                    result.add("+")
                    result.add("-")
                    result.add("0")
        return SignSet(signs = result)

    @staticmethod
    def abstract(items: set[int]):
        result = set()
        for item in items:
            if item > 0:
                result.add("+")
            elif item < 0:
                result.add("-")
            else:
                result.add("0")
        return SignSet(signs = result)

    def __contains__(self, x: int):
        if x > 0:
            return "+" in self.signs
        elif x < 0:
            return "-" in self.signs
        else:
            return "0" in self.signs

    def __iter__(self): 
        return iter(self.signs)


s1 = SignSet(signs = {"+", "-"})
s2 = SignSet(signs = {"-", "0"})
s3 = SignSet(signs = {"+"})
s4 = SignSet(signs = {"0", "+"})

print(s1 & s2) # SignSet(signs={'-'})
print(s1 | s2) # SignSet(signs={'+', '-', '0'})
print(s1 <= s2) # False
print(s3 <= s1) # True
print(s1 + s2) # SignSet(signs={'+', '-', '0'})
print(s3 + s3) # SignSet(signs={'+', '+'})
print(s4 + s3) # SignSet(signs={'+'})
print("abstract and contains")
print(SignSet.abstract({1, 2, 3})) # SignSet(signs={'+'})
print(SignSet.abstract({-1, -2, -3})) # SignSet(signs={'-'})
print(SignSet.abstract({0, 1, 2, 3})) # SignSet(signs={'+', '0'})
print(SignSet.abstract({0, -1, -2, -3})) # SignSet(signs={'-', '0'})
print(SignSet.abstract({0})) # SignSet(signs={'0'})
print(SignSet.abstract({-1, 1, 0})) # SignSet(signs={'+', '0', '-'})
print(1 in s1) # True
print(0 in s1) # False
print(-1 in s1) # True

    
@given(sets(integers()), sets(integers()))
def test_sign_adds(xs, ys):
  assert (
    SignSet.abstract({x + y for x in xs for y in ys}) 
      <= SignSet.abstract(xs) + SignSet.abstract(ys)
    )
  
@given(sets(integers()), sets(integers()))
def test_sign_le(xs, ys):
    assert (
      {x <= y for x in xs for y in ys} 
      <= (set.union(set(), *[
          SignHelper(sign = x) <= SignHelper(sign = y) for x in SignSet.abstract(xs) for y in SignSet.abstract(ys)
          ]))
    )