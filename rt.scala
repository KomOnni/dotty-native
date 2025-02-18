import java.io.{FileOutputStream, IOException}
import java.nio.file.{FileSystems, Files}
import java.util.zip.{ZipEntry, ZipError, ZipException, ZipOutputStream}
import scala.jdk.CollectionConverters.*
import scala.util.control.NonFatal

//If you need another java module, just add it here
val buildModules = Vector(
"java.base",
"java.desktop",
)

@main def extractRTJar: Unit = {
  val fs = FileSystems.getFileSystem(java.net.URI.create("jrt:/"))

  val zipStream = new ZipOutputStream(new FileOutputStream("extracted-rt.jar"))
  try {
    for (moduleName <- buildModules) {
        val javaModulePath = fs.getPath("modules", moduleName)
        //There is one common file in all modules which causes ZipException, but is not needed
        //This checks that ZipException does not happen more than once
        var failedCounter = 0
        Files.walk(javaModulePath).forEach({ p =>
        if (Files.isRegularFile(p)) {
            try {
            val data = Files.readAllBytes(p)
            val outPath = javaModulePath.relativize(p).iterator().asScala.mkString("/")
            val ze = new ZipEntry(outPath)
            zipStream.putNextEntry(ze)
            zipStream.write(data)
            } catch {
            case a: ZipException =>
                failedCounter += 1 
                if failedCounter > 1 then
                  throw new ZipException
            case NonFatal(t) =>
                throw new IOException(s"Exception while extracting $p", t)
            }
        }
        })
    }
  } finally {
    zipStream.close()
  }
}
