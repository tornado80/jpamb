package jpamb.utils;

import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public record CaseContent(
    Object[] params,
    Class<? extends Throwable> raises) {

  public static CaseContent parse(String string) {
    Pattern pattern = Pattern.compile("\\(([^)]*)\\)\\s*->\\s*(.+)");
    Matcher matcher = pattern.matcher(string);

    // Parse the expression
    if (matcher.find()) {
      String args = matcher.group(1);
      String result = matcher.group(2);
      ArrayList<Object> list = new ArrayList<>();
      try (Scanner sc = new Scanner(args)) {
        while (sc.hasNext()) {
          if (sc.hasNextBoolean()) {
            list.add(sc.nextBoolean());
          } else {
            String var = sc.next();
            if (!var.equals(",")) {
              throw new RuntimeException("Invalid case: " + string + " // unexpected " + var);
            }
          }
        }
      }
      if (result.equals("assertion error")) {
        return new CaseContent(list.toArray(), AssertionError.class);
      } else {
        throw new RuntimeException("Invalid case: " + string);
      }
    } else {
      throw new RuntimeException("Invalid case: " + string);
    }
  }
}
