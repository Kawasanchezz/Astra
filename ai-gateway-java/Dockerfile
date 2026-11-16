FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B -q dependency:go-offline
COPY src src
RUN mvn -B -q -DskipTests package

FROM eclipse-temurin:21-jre
RUN useradd --system --uid 10001 --no-create-home app
WORKDIR /app
COPY --from=build /app/target/ai-gateway.jar app.jar
USER app
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
