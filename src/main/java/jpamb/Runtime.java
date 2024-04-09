package jpamb;

import java.lang.reflect.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Stream;

import jpamb.utils.*;
import jpamb.cases.*;

public class Runtime {

  public static Case[] cases(Method m) {
    var cases = m.getAnnotation(Cases.class);
    if (cases == null) {
      var c = m.getAnnotation(Case.class);
      if (c == null)
        return new Case[] {};
      return new Case[] { c };
    } else {
      return cases.value();
    }
  }

  public static void main(String[] args) throws ClassNotFoundException, InterruptedException {
    var mths = Stream.of(Simple.class, Loops.class).flatMap(c -> Stream.of(c.getMethods())).toList();
    for (Method m : mths) {
      for (Case c : cases(m)) {
        CaseContent content = CaseContent.parse(c.value());

        if (!Modifier.isStatic(m.getModifiers())) {
          System.out.println("Method is not static");
          continue;
        }

        String id = m.getDeclaringClass().getName() + "." + m.getName() + content + ":";
        System.out.printf("%-80s", id);
        System.out.flush();
        final AtomicReference<Throwable> atom = new AtomicReference<>();
        Thread t = new Thread(() -> {
          try {
            m.invoke(null, content.params());
          } catch (InvocationTargetException e) {
            atom.set(e.getCause());
          } catch (IllegalAccessException e) {
            atom.set(e);
          }
        });
        t.start();
        t.join(100);

        if (t.isAlive())
          t.stop();

        Throwable error = atom.get();
        if (t.isAlive() && error == null) {
          error = new TimeoutException();
        }

        String message;
        if (error == null) {
          message = "did not produce error";
        } else if (content.result().expectThrows(error.getClass())) {
          message = "success";
        } else {
          message = error.toString();
        }
        System.out.printf("%s%n", message);
      }
    }
  }
}
