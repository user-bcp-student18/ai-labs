package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

@QuarkusTest
class AuthResourceTest {
    private static final String INJECTION_VALUE = "' OR '1'='1";

    @Test
    void rejectsInjectionShapedUsername() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"" + INJECTION_VALUE + "\",\"password\":\"not-the-password\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void rejectsInjectionShapedPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"" + INJECTION_VALUE + "\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("token", notNullValue());
    }
}
