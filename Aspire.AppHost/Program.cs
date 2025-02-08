using Microsoft.Extensions.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

var portValueStr = Environment.GetEnvironmentVariable("UVICORN_PORT");
var portValueInt = int.TryParse(portValueStr, out int portParsed) ? portParsed : 8111;

// Python Hosting은 실험적 기능으로, 추가 방법이 바뀔 수 있어 Warning을 띄움. 테스트 용도로만 사용이 권장됨.
#pragma warning disable ASPIREHOSTINGPYTHON001
var uvicornApp = builder.AddUvicornApp(
        name: "python",                // Name of the Python project
        projectDirectory: "../python", // Path to the Python project
        appName: "app:app",            // {FILE_NAME}:{APP_VARIABLE_NAME}
        args: new[] { 
            "--reload"
        }
    )
    // 무조건 환경변수로 지정된 PORT를 따라가는 이슈가 있어 export PORT=8000 같이 지정해줌
    .WithHttpEndpoint(
        targetPort: portValueInt,      // tatgetPort : Port the resource is listening on
        port: portValueInt + 1         // port : Port that will be exposed to the outside
    );
#pragma warning restore ASPIREHOSTINGPYTHON001

builder.Build().Run();
