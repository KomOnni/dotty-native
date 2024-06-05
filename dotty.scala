//> using scala "3.4.1"
//> using dep "org.scala-lang::scala3-compiler:3.4.1"
@main def main(args: String*) = dotty.tools.dotc.Main.process(args.toArray)