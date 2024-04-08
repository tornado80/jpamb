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

}
