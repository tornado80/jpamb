package jpamb.utils;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Scanner;
import java.util.concurrent.TimeoutException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public record CaseContent(
    Object[] params,
    ResultType result) {

  public String toString() {
    List<String> sparams = Arrays.asList(params).stream().map(a -> a.toString()).toList();

    return "(" + String.join(", ", sparams) + ") -> " + result.toString();
  }

  public static CaseContent parse(String string) {
    Pattern pattern = Pattern.compile("\\(([^)]*)\\)\\s*->\\s*(.+)");
    Matcher matcher = pattern.matcher(string);

    // Parse the expression
    if (matcher.find()) {
      String args = matcher.group(1);
      String result = matcher.group(2);
      ArrayList<Object> list = new ArrayList<>();
      try (Scanner sc = new Scanner(args)) {
        sc.useLocale(Locale.US);
        sc.useDelimiter(" *, *");
        while (sc.hasNext()) {
          if (sc.hasNextBoolean()) {
            list.add(sc.nextBoolean());
          } else if (sc.hasNextInt()) {
            list.add(sc.nextInt());
          } else {
            String var = sc.next();
            if (!var.equals(",")) {
              throw new RuntimeException("Invalid case: " + string + " // unexpected " + var);
            }
          }
        }
      }
      return new CaseContent(list.toArray(), ResultType.parse(result));
    } else {
      throw new RuntimeException("Invalid case: " + string);
    }
  }

  public static enum ResultType {
    DIVIDE_BY_ZERO,
    ASSERTION_ERROR,
    NON_TERMINATION;

    public static ResultType parse(String string) {
      if (string.equals("*")) {
        return NON_TERMINATION;
      } else if (string.equals("assertion error")) {
        return ASSERTION_ERROR;
      } else if (string.equals("divide by zero")) {
        return DIVIDE_BY_ZERO;
      } else {
        throw new RuntimeException("Invalid result type: " + string);
      }
    }

    public String toString() {
      switch (this) {
        case DIVIDE_BY_ZERO:
          return "divide by zero";
        case ASSERTION_ERROR:
          return "assertion error";
        case NON_TERMINATION:
          return "*";
        default:
          throw new RuntimeException("Unexpected");
      }
    }

    public boolean expectThrows(Class<? extends Throwable> clazz) {
      switch (this) {
        case DIVIDE_BY_ZERO:
          return clazz.equals(ArithmeticException.class);
        case ASSERTION_ERROR:
          return clazz.equals(AssertionError.class);
        case NON_TERMINATION:
          return clazz.equals(TimeoutException.class);
        default:
          throw new RuntimeException("Unexpected");
      }
    }
  }
}
