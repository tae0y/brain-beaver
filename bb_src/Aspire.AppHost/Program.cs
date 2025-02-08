using Microsoft.Extensions.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

var portValueStr = Environment.GetEnvironmentVariable("UVICORN_PORT");
var portValueInt = int.TryParse(portValueStr, out int portParsed) ? portParsed : 8111;

var apsolutepath_portainer_volume = Path.GetFullPath("../../bb_docker/portainer").Replace("\\", "/");
var apsolutepath_postgresql_volume = Path.GetFullPath("../../bb_docker/postgresql").Replace("\\", "/");
var apsolutepath_initd_volume = Path.GetFullPath("../../bb_docker/init.d").Replace("\\", "/");
var apsolutepath_pgadmin_volume = Path.GetFullPath("../../bb_docker/pgadmin").Replace("\\", "/");

var portainerContainer = builder.AddDockerfile(
        "dockeradmin",   
        "../../bb_docker",          // 도커파일이 위치한 디렉토리 상대경로 (AppHost.csproj 기준)
        "Dockerfile-dockeradmin"    // 도커파일 이름
    )
    .WithContainerName("dockeradmin")
    .WithHttpEndpoint(9000, 9000)
    .WithVolume(apsolutepath_portainer_volume, "/data");
var postgresqlContainer = builder.AddDockerfile(
        "bwsdb",
        "../../bb_docker",
        "Dockerfile-dockeradmin"
    )
    .WithContainerName("bwsdb")
    .WithEnvironment("POSTGRES_USER", "root")
    .WithEnvironment("POSTGRES_PASSWORD", "root")
    .WithEnvironment("POSTGRES_DB", "bwsdb")
    .WithHttpEndpoint(5432, 5432)
    .WithVolume(apsolutepath_postgresql_volume, "/var/lib/postgresql/data")
    .WithVolume(apsolutepath_initd_volume, "/docker-entrypoint-initdb.d");
var pgadminContainer = builder.AddDockerfile(
        "bwsdbadmin", 
        "../../bb_docker",
        "Dockerfile-dockeradmin"
    )
    .WithContainerName("bwsdbadmin")
    .WithEnvironment("PGADMIN_DEFAULT_EMAIL", "admin@ta0y.com")
    .WithEnvironment("PGADMIN_DEFAULT_PASSWORD", "admin")
    .WithVolume(apsolutepath_pgadmin_volume, "/var/lib/pgadmin");

// Python Hosting은 실험적 기능으로, 추가 방법이 바뀔 수 있어 Warning을 띄움. 테스트 용도로만 사용이 권장됨.
#pragma warning disable ASPIREHOSTINGPYTHON001
var uvicornApp = builder.AddUvicornApp(
        name: "python",                        // Name of the Python project
        projectDirectory: "../Python.FastApi", // Path to the Python project
        appName: "app:app",                    // {FILE_NAME}:{APP_VARIABLE_NAME}
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
