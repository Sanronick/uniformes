import sqlite3
from flask import Flask, jsonify, request,url_for,render_template
from flask_cors import CORS

DATABASE='inventario_uniformes.db'

def get_db_connection():
    conn=sqlite3.connect(DATABASE)
    conn.row_factory=sqlite3.Row
    return conn

#Creo la tabla Uniformes

def create_table():
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uniformes(
                   codigo INTEGER PRIMARY KEY,
                   descripcion TEXT NOT NULL,
                   talle TEXT NOT NULL,
                   cantidad INTEGER NOT NULL,
                   proveedor TEXT NOT NULL,
                   ubicacion TEXT NOT NULL,
                   estado TEXT NOT NULL
        )''')

#Creo la base de datos y la tabla

def create_database():
    conn=sqlite3.connect(DATABASE)
    conn.close()
    create_table()

create_database()


class Uniformes:
    #Manejo de stock uniformes
    def __init__(self,codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado):
        self.codigo=codigo
        self.descripcion=descripcion
        self.talle=talle
        self.cantidad=cantidad
        self.proveedor=proveedor
        self.ubicacion=ubicacion
        self.estado=estado

    def modificar(self,ndescripcion,ntalle,ncantidad,nproveedor,nubicacion,nestado):
        self.descripcion=ndescripcion
        self.talle=ntalle
        self.cantidad=ncantidad
        self.proveedor=nproveedor
        self.ubicacion=nubicacion
        self.estado=nestado



#Inventario de Uniformes
class Inventario:
    def __init__(self):
        self.conexion=get_db_connection()
        self.cursor=self.conexion.cursor()
    
    def agregar_uniforme(self,codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado):
        uniforme_existente=self.consultar_uniforme(codigo)
        if uniforme_existente:
            return jsonify({'message':'Ya existe un uniforme con ese codigo.'}),400
        sql=f'INSERT INTO uniformes VALUES({codigo},"{descripcion}","{talle}",{cantidad},"{proveedor}","{ubicacion}","{estado}");'
        self.cursor.execute(sql)
        self.conexion.commit()
        return jsonify({'message':'Uniforme agregado correctamente.'}),200

    # Este método permite consultar datos de productos que están en el inventario 
    # Devuelve el producto correspondiente al código proporcionado o False si no existe.

    def consultar_uniforme(self,codigo):
        sql=f'SELECT * FROM uniformes WHERE codigo = {codigo};'
        self.cursor.execute(sql)
        row=self.cursor.fetchone()
        if row:
            codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado=row
            return Uniformes(codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado)
        return None
        
    
    def modificar_uniforme(self,codigo,ndescripcion,ntalle,ncantidad,nproveedor,nubicacion,nestado):
        uniforme=self.consultar_uniforme(codigo)
        if uniforme:
            uniforme.modificar(ndescripcion,ntalle,ncantidad,nproveedor,nubicacion,nestado)
            sql=f'UPDATE uniformes SET descripcion="{ndescripcion}",talle="{ntalle}",cantidad={ncantidad},proveedor="{nproveedor}",ubicacion="{nubicacion}",estado="{nestado}" WHERE codigo={codigo};'
            self.cursor.execute(sql)
            self.conexion.commit()
            return jsonify({'message':'Uniforme modificado correctamente.'}),200
        return jsonify({'message':'Uniforme no encontrado'}),404
            
    def eliminar_uniforme(self,codigo):
        sql=f'DELETE FROM uniformes WHERE codigo={codigo}'
        self.cursor.execute(sql)
        if self.cursor.rowcount>0:
            self.conexion.commit()
            return jsonify({'message':'Uniforme eliminado correctamente.'}),200
        return jsonify({'message':'Uniforme no encontrado'}),404
            
        

    
    def listar_uniformes(self):
        self.cursor.execute('SELECT * FROM uniformes')
        rows=self.cursor.fetchall()
        uniformes=[]
        for row in rows:
            codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado=row
            uniforme={'codigo':codigo,'descripcion':descripcion,'talle':talle,'cantidad':cantidad,'proveedor':proveedor,'ubicacion':ubicacion,'estado':estado}
            uniformes.append(uniforme)
        return jsonify(uniformes),200


#Salidas
class Salidas:

    def __init__(self):
        self.conexion=get_db_connection()
        self.cursor=self.conexion.cursor()
        self.items=[]

    def agregar_salida(self,codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado,inventario):
        uniforme=inventario.consultar_uniforme(codigo)

        if uniforme is None:
            return jsonify({'message':'El uniforme no existe'}),404
        
        #Chequea si hay talles de ese uniforme
        if uniforme.talle!=talle:
            return jsonify({'message':'No hay talles de ese uniforme'}),400
        
        #Chequea si hay cantidad en stock
        if uniforme.cantidad<cantidad:
            return jsonify({'message':'Cantidad en stock insuficiente'}),400
        
        #Chequea si el uniforme ya está en salidas
        for item in self.items:
            if item.codigo==codigo:
                #si existe, sumo a la cantidad de las salidas
                item.cantidad+=cantidad
                #..y descuento del stock de uniformes de la BB.DD.
                sql=f'UPDATE uniformes SET descripcion={descripcion},talle={talle},cantidad=cantidad-{cantidad},proveedor={proveedor},ubicacion={ubicacion},estado={estado} WHERE codigo={codigo};'
                self.cursor.execute(sql)
                self.conexion.commit()
                return jsonify({'message':'Uniforme agregado a salidas correctamente'}),200
            
        #si el uniforme no esta en salidas, se agrega como un nuevo item
        nuevo_item=Uniformes(codigo,uniforme.descripcion,talle,cantidad,uniforme.proveedor,uniforme.ubicacion,uniforme.estado)
        self.items.append(nuevo_item)

        #Actualizamos la cantidad en la BB.DD
        sql=f'UPDATE uniformes SET descripcion={descripcion},talle={talle},cantidad=cantidad-{cantidad},proveedor={proveedor},ubicacion={ubicacion},estado={estado} WHERE codigo={codigo};'
        self.cursor.execute(sql)
        self.conexion.commit()
        return jsonify({'message':'Uniforme agregado a salidas correctamente'}),200
    

        

    def quitar_salida(self,codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado,inventario):
            
            for item in self.items:
       
            #Si encuentra ese uniforme
                if item.codigo==codigo:
                    #Si no hay de ese talle en entrega
                    if item.talle!=talle:
                        return jsonify({'message':'No hay de ese talle en Entrega'}),400
                    elif cantidad>item.cantidad:
                        return jsonify({'message':'Cantidad a quitar mayor a la que está en Entrega'}),400
                    item.cantidad-=cantidad
                    if item.cantidad==0:
                        self.items.remove(item)
                     #Actualizamos la cantidad en la BB.DD

                    sql=f'UPDATE uniformes SET descripcion={descripcion},talle={talle},cantidad=cantidad+{cantidad},proveedor={proveedor},ubicacion={ubicacion},estado={estado} WHERE codigo={codigo};'
                    self.cursor.execute(sql)
                    self.conexion.commit()
                    return jsonify({'message':'Uniforme quitado de salidas exitosamente'}),200
                return jsonify({'message':'El uniforme no se encuentra en salidas'}),404

                    
            #Si el for termina sin novedad, es que ese uniforme no esta en Entrega
            return jsonify({'message':'El uniforme no se encuentra en salidas'}),404

    def mostrar_salida(self):
        uniformes_salidas=[]
        for item in self.items:
            uniforme={'codigo':item.codigo,'descripcion':item.descripcion,'talle':item.talle,'cantidad':item.cantidad,'proveedor':item.proveedor,'ubicacion':item.ubicacion,'estado':item.estado}
            uniformes_salidas.append(uniforme)
        return jsonify(uniformes_salidas),200


app=Flask(__name__)
CORS(app)
salidas=Salidas()
inventario=Inventario()

#Ruta para obtener los datos de un uniforme segun su codigo
@app.route('/uniformes/<int:codigo>', methods=['GET'])
def obtener_uniforme(codigo):
    uniforme=inventario.consultar_uniforme(codigo)
    if uniforme:
        return jsonify({
            'codigo':uniforme.codigo,
            'descripcion':uniforme.descripcion,
            'talle':uniforme.talle,
            'cantidad':uniforme.cantidad,
            'proveedor':uniforme.proveedor,
            'ubicacion':uniforme.ubicacion,
            'estado':uniforme.estado
        }),200
    return jsonify({'message':'Uniforme no encontrado'}),404

#Ir al Index
@app.route('/')
def index():
    return 'API Uniformes'

#Ruta para obtener la lista de Uniformes del Inventario
@app.route('/uniformes',methods=['GET'])
def obtener_uniformes():
    return inventario.listar_uniformes()

#Ruta para agregar un uniforme al inventario
@app.route('/uniformes',methods=['POST'])
def agregar_uniforme():
    codigo=request.json.get('codigo')
    descripcion=request.json.get('descripcion')
    talle=request.json.get('talle')
    cantidad=request.json.get('cantidad')
    proveedor=request.json.get('proveedor')
    ubicacion=request.json.get('ubicacion')
    estado=request.json.get('estado')
    return inventario.agregar_uniforme(codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado)

#Ruta para modificar un uniforme del inventario
@app.route('/uniformes/<int:codigo>',methods=['PUT'])
def modificar_uniforme(codigo):
    ndescripcion=request.json.get('descripcion')
    ntalle=request.json.get('talle')
    ncantidad=request.json.get('cantidad')
    nproveedor=request.json.get('proveedor')
    nubicacion=request.json.get('ubicacion')
    nestado=request.json.get('estado')
    return inventario.modificar_uniforme(codigo,ndescripcion,ntalle,ncantidad,nproveedor,nubicacion,nestado)


#Ruta para eliminar un uniforme del inventario
@app.route('/uniformes/<int:codigo>',methods=['DELETE'])
def eliminar_uniforme(codigo):
    return inventario.eliminar_uniforme(codigo)

#Agrego a Salidas
@app.route('/salidas',methods=['POST'])
def agregar_salida():
    codigo=request.json.get('codigo')
    descripcion=request.json.get('descripcion')
    talle=request.json.get('talle')
    cantidad=request.json.get('cantidad')
    proveedor=request.json.get('proveedor')
    ubicacion=request.json.get('ubicacion')
    estado=request.json.get('estado')
    inventario=Inventario()
    return salidas.agregar_salida(codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado,inventario)

#Elimino de Salidas
@app.route('/salidas',methods=['DELETE'])
def quitar_salida():
    codigo=request.json.get('codigo')
    descripcion=request.json.get('descripcion')
    talle=request.json.get('talle')
    cantidad=request.json.get('cantidad')
    proveedor=request.json.get('proveedor')
    ubicacion=request.json.get('ubicacion')
    estado=request.json.get('estado')
    inventario=Inventario()
    return salidas.quitar_salida(codigo,descripcion,talle,cantidad,proveedor,ubicacion,estado,inventario)

#Ruta para ver el carrito
@app.route('/salidas',methods=['GET'])
def mostrar_salida():
    return salidas.mostrar_salida()

if __name__=='__main__':
    app.run()
