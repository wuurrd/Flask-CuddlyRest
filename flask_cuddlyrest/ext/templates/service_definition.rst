
   * **GET {{ url }}**

     Retrieve the list of all records.

     Result:

         - Body: A JSON list of `{{ document }}` objects.


   * **POST {{ url }}**

     Create a new record.

     Expected Input:

         - Headers:

            - *content-type*: application/json

         - Body:

            The JSON definition of the `{{ document }}` object to be created.
            It can be a partial definition. Some members may be required.

     Result:

         - *201 (CREATED)* upon succesful creation.

   * **GET {{ url }}/<id>**

     Retrieve a designated record.

     Expected Input:

         - Url parameters:

            - *id*: The MongoDB ObjectID that uniquely identifies the record.

     Result:

         - *200 (OK)* if found.

           Body: The `{{ document }}` JSON object describing the matched object.

         - *404 (NOT FOUND)* if not found.

   * **DELETE {{ url }}/<id>**

     Delete a designated record.

     Expected Input:

         - Url parameters:

            - *id*: The MongoDB ObjectID that uniquely identifies

     Result:

         - *200 (OK)* if deleted.
         - *404 (NOT FOUND)* if no matching record to delete could be found.

   * **PUT {{ url }}/<id>**

     .. warning::
         TODO: Change the method to PATCH instead.
     ..

     Do a partial update on the designated record.

     Expected Input:

         - Headers:

            - *content-type*: application/json

         - Body: The JSON definition of the modification to the target `{{ document }}` object.

     Result:

         - *200 (OK)* upon succesful update.

           Body: The  `{{ document }}` JSON object if succesfully found.

         - *404 (NOT FOUND)* if no matching record to update could be found.
