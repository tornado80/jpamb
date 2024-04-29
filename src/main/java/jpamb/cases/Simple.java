package jpamb.cases;

import jpamb.utils.Case;

public class Simple {

  @Case("() -> assertion error")
  public static void assertFalse() {
    assert false;
  }

  @Case("(false) -> assertion error")
  public static void assertBoolean(boolean shouldFail) {
    assert shouldFail;
  }

  @Case("(0) -> assertion error")
  public static void assertInteger(int n) {
    assert n != 0;
  }

  @Case("(-1) -> assertion error")
  public static void assertPositive(int num) {
    assert num > 0;
  }

  @Case("() -> divide by zero")
  public static int divideByZero() {
    return 1 / 0;
  }

  @Case("(0) -> divide by zero")
  public static int divideByN(int n) {
    return 1 / n;
  }

  @Case("(0, 0) -> divide by zero")
  public static int divideZeroByZero(int a, int b) {
    return a / b;
  }

  @Case("(false) -> assertion error")
  @Case("(true) -> divide by zero")
  public static int multiError(boolean b) {
    assert b;
    return 1 / 0;
  }

}
