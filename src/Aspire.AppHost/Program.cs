using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.Extensions.Hosting;
using Microsoft.VisualBasic;

var builder = DistributedApplication.CreateBuilder(args);


/****************************************************************************************
 * 
 *  OpenTelemetry
 * 
 ****************************************************************************************/





/****************************************************************************************
 * 
 *  Health Check
 * 
 ****************************************************************************************/

var pythonPortStr = Environment.GetEnvironmentVariable("UVICORN_PORT");
int pythonPort = int.TryParse(pythonPortStr, out int pythonPortParsed) ? pythonPortParsed : 8111;

// python-health-check
builder.Services.AddHealthChecks().AddCheck("python-health-check", 
    () =>  {
        try {
            using var client = new System.Net.Http.HttpClient();
            client.Timeout = TimeSpan.FromSeconds(2);
            var response = client.GetAsync($"http://localhost:{pythonPort}")
                                 .GetAwaiter()
                                 .GetResult();
            return response.StatusCode == System.Net.HttpStatusCode.OK 
                ? HealthCheckResult.Healthy("Python App running") 
                : HealthCheckResult.Unhealthy("Python App something wrong");
        }
        catch (System.Exception ex) {
            return HealthCheckResult.Unhealthy("Python App something wrong : " + ex.Message);
        }
    },
    tags: new[] { "python" }
);


/****************************************************************************************
 * 
 *  Docker Container Hosting
 * 
 ****************************************************************************************/

// AppHost의 DockerContainer는 상대경로 기반 Volume을 제공하지 않음
// 디렉토리명만 제공시 OrbStack/Docker/Volume 아래 생성됨
var apsolutepath_initdbd_volume     = Path.GetFullPath("../../docker/initdb.d");
var justdirectory_portainer_volume  = "portainer_volume";
var justdirectory_postgresql_volume = "postgresql_volume";
var justdirectory_pgadmin_volume    = "pgadmin_volume";

var portainerContainer = builder.AddDockerfile(
        "dockeradmin",
        "../../docker",          // 도커파일이 위치한 디렉토리 상대경로 (AppHost.csproj 기준)
        "Dockerfile-dockeradmin" // 도커파일 이름
    )
    .WithContainerName("bwscontaineradmin")
    .WithHttpEndpoint(port:9000, targetPort:9000)
    .WithVolume(justdirectory_portainer_volume, "/data");

var postgresqlContainer = builder.AddDockerfile(
        "bwsdb",
        "../../docker",
        "Dockerfile-bwsdb"
    )
    .WithContainerName("bwsdb")
    .WithEnvironment("POSTGRES_USER", "root")
    .WithEnvironment("POSTGRES_PASSWORD", "root")
    .WithEnvironment("POSTGRES_DB", "bwsdb")
    .WithEndpoint(port:5432, targetPort:5432)
    .WithVolume(justdirectory_postgresql_volume, "/var/lib/postgresql/data")
    .WithBindMount(apsolutepath_initdbd_volume, "/docker-entrypoint-initdb.d");

var pgadminContainer = builder.AddDockerfile(
        "bwsdbadmin",
        "../../docker",
        "Dockerfile-bwsdbadmin"
    )
    .WithContainerName("bwsdbadmin")
    .WithEnvironment("PGADMIN_DEFAULT_EMAIL", "admin@ta0y.com")
    .WithEnvironment("PGADMIN_DEFAULT_PASSWORD", "admin")
    .WithHttpEndpoint(port:5050, targetPort:80)
    .WithVolume(justdirectory_pgadmin_volume, "/var/lib/pgadmin");

var rabbitMQContainer = builder.AddDockerfile(
        "rabbitmq",
        "../../docker",
        "Dockerfile-bwsmq"
    )
    .WithContainerName("bwsmq")
    .WithEndpoint(port:5672, targetPort:5672)
    .WithHttpEndpoint(port:15672,targetPort:15672)
    .WithVolume("rabbitmq_volume", "/var/lib/rabbitmq");


/****************************************************************************************
 * 
 *  Python Application Hosting
 * 
 ****************************************************************************************/

// Python Hosting은 실험적 기능으로, 추가 방법이 바뀔 수 있어 Warning을 띄움. 테스트 용도로만 사용이 권장됨.
#pragma warning disable ASPIREHOSTINGPYTHON001
var pythonApp = builder.AddPythonApp(
        name: "python",
        projectDirectory: "../Python.FastAPI",
        virtualEnvironmentPath: "../Python.FastAPI/.venv",
        scriptPath: "app.py",
        scriptArgs: new[] {""}
    )
    .WithHttpEndpoint(
        targetPort: pythonPort,
        port: pythonPort+1)
    .WaitFor(rabbitMQContainer)
    .WaitFor(postgresqlContainer)
    .WithHealthCheck("python-health-check"); // 30초마다 헬스체크, 타임아웃 2초, 실패시 3번 재시도

//var uvicornApp = builder.AddUvicornApp(
//        name: "python",                        // Name of the Python project
//        projectDirectory: "../Python.FastAPI", // Path to the Python project
//        appName: "app:app",                    // {FILE_NAME}:{APP_VARIABLE_NAME}
//        args: new[] { 
//            "--reload"
//        }
//    )
//    // 무조건 환경변수로 지정된 PORT를 따라가는 이슈가 있어 export PORT=8000 같이 지정해줌
//    .WithHttpEndpoint(
//        targetPort: portValueInt,      // tatgetPort : Port the resource is listening on
//        port: portValueInt             // port : Port that will be exposed to the outside
//    )
//    .WaitFor(rabbitMQContainer)
//    .WaitFor(postgresqlContainer);
#pragma warning restore ASPIREHOSTINGPYTHON001


/****************************************************************************************
 * 
 *  Build and Run
 * 
 ****************************************************************************************/
builder.Build().Run();
