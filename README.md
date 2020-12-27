# mail-lang

That's a crappy compiler of a crappy language.
Mail-lang is an esoteric programming language whose control flow is defined by emails:

* you want to set a variable? Email it the value.
* You want to call a function? Email it the arguments.
* You want to read the result of the function? Reply to the sent email.

This README is also crappy.
I got this idea a long time ago and I'm only uploading it for giggles.

You can find in `examples/fibonacci.mail` a program that computes the fibonacci number of the user's stdin input.

Interesting domains to lookout for are: `...@local`, `...@global`, `...@arguments`, and `...@continuations`
