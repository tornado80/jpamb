package jpamb;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

import jpamb.utils.Case;
import jpamb.utils.CaseContent;

public class Runtime {

  public static void main(String[] args) throws ClassNotFoundException {
    var cls = Class.forName("jpamb.cases.Simple");
    for (Method m : cls.getMethods()) {
      var c = m.getAnnotation(Case.class);
      if (c == null)
        continue;

      CaseContent content;
      content = CaseContent.parse(c.value());

      if (!Modifier.isStatic(m.getModifiers())) {
        System.out.println("Method is not static");
        continue;
      }

      String message = null;
      try {
        m.invoke(null, content.params());
      } catch (IllegalAccessException e) {
        e.printStackTrace();
      } catch (InvocationTargetException e) {
        Class<? extends Throwable> clazz = e.getCause().getClass();
        if (content.result().expectThrows(clazz)) {
          message = "success";
        } else {
          message = e.getCause().toString();
        }
      }

      if (message == null) {
        message = "did not produce error";
      }

      System.out.println(cls.getName() + "." + m.getName() + content + ": " + message);

    }
  }
}
